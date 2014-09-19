---
layout: post
title: Metrics 的实时监控
date: 2014-09-19 17:31
author: hit9
categories: tech
---

通过向程序嵌入metrics我们可以获悉服务的运行状态，指标可以是接口的调用次数、调用的时长、异常
的个数等等，那我们如何对metrics做监控呢？

本博文用以记录我们的metric监控项目[node-bell](https://github.com/eleme/node-bell)。

如何判断数据的异常？
--------------------

最简单的办法是设置上下阈值，当数据不在阈值范围内的时候认为是异常的。

但是，阈值设成多少好呢？？不要说metrics千千万，挨个设置很费事的，就单个的metric来讲，设的大小也要琢磨
一番。不能太严格，也不要太宽松，那么多少才算合适呢？

Node-bell采用一个简单的统计学原理来动态的给出阈值，3-sigma准则，也叫做68-95-99.7准则：
> 正态分布中，99.7%的数据分布在偏离平均水平3倍的标准差的范围内。

也就是说，如果一个数据点偏离平均水平超过了3倍标准差，那么它很可能是异常的，用伪代码来描述的话就是这样的:

```javascript
funtion isAnomaly(val) {
    return abs(val - mean) > 3 * std;
}
```

这样，我们可以根据历史数据动态地给出新生数据点的阈值范围了。 下左图表示固定阈值，下右图表示动态阈值。
![](https://cloud.githubusercontent.com/assets/290496/4334182/78d642d6-3fea-11e4-9918-954784ea163f.jpg)

异常程度的描述
--------------

在大量的metrics中，我们只关心异常更严重的那部分，因此node-bell需要一个数字来描述异常的严重程度，
那么，我们定义一个叫做异常程度的东西，它是数据点对平均水平的偏离与3倍标准差的比：

```javascript
m = abs(val - mean) / (3 * std)
```

因此m大于1的数据点是异常的，m越大，异常越严重。

这个异常程度m就是node-bell每次计算要的结果。

周期性数据的异常检测
--------------------

现实中的数据大多是周期性的，比如饿了么一天的订单量，肯定会出现日周期，我们会在用餐时段出现小高峰。

异常数据的检测需要考虑数据的周期性吗？是的，一个例子如图：

![](https://cloud.githubusercontent.com/assets/1687443/4334353/a9ede394-3fed-11e4-9915-4262f2aefe01.png)

上图中被圈的数据点在总体范围来看，是符合阈值要求的，但是由于数据有周期性，它被认为成异常的。举例说，
我们饿了么是不会在夜间达到中午的订单量的。

解决办法就是消去周期性，按周期取出同相位的数据点，然后再用3-sigma判断异常性。


Node-bell的实现
----------------

### 组件与数据流

```javascript
[statsd]->[listener]->[beanstalkd]
                           |
                           v
            --------> [analyzers] ------> [alerter]
            |              |
    history |         save v    visualize
            ------------ [ssdb] --------> [webapp]
```

目前node-bell有4个组件(叫做服务也好):

- listener，负责接收metrics和Job入队
- analyzer，负责异常分析和结果存储
- webapp，负责分析结果可视化
- alerter，负责报警

数据来自[StatsD](https://github.com/etsy/statsd)，它是metrics的聚合工具，可以把聚合结果发送到多个后端。

因为Analyzer的复杂度较高、IO次数多，所以Analyzer设计为可以跑多个worker。

### 数据的存储

Node-bell使用[ssdb](https://github.com/ideawu/ssdb)来存储数据，这是一个类似Redis的数据结构服务器。
选择它的原因主要有：

- 支持Sorted Set，可以做典型的[时间序列存储](https://github.com/eleme/node-bell#storage).
- 内存占用可设上限，因此选择ssdb而非redis.
- 据说支持大量数据的存储. （node-bell要写多少数据啊？Eleme现在不到5天的数据60G）

就目前跑的情况来看，ssdb的表现非常不错，node-bell用起来单实例足够。

对Metric趋势的观察
------------------

数据的查询需求决定了数据的存储。那node-bell的数据查询需求是怎样的？

简单来说，及时地观察到目前异常的metric。ops上，就是及时发现异常，找到出问题的接口:

- 如果时长数据异常了，意味着接口超时
- 如果调用量异常了，意味着可能有刷站行为

那么，我们需要关注那些最近时段内异常程度较高的metric，然后观察它高在了哪里。

Webapp组件使用了[Cubism](http://square.github.com/cubism/)来可视化数据，大致的效果如下：

![](https://github.com/eleme/node-bell/raw/master/snap.png)

### 如何做Trending

Reddit有自己的trending, GitHub有自己的trending.. Trending可以反映最近时间内上升较快的数据。

Node-bell最初使用最近一段时间(如5min)内异常点的个数来实现trending，但是这样做就需要
同时查询多个Sorted Set的count，然后排序输出，有1k个metric，就需要1k次查询。现在node-bell使用
加权移动平均值来描述trending, 然后使用Sorted Set来存储metrics的trending. 这样，每次查询
trending，仅需一次数据库查询。

所谓加权移动平均的办法，就node-bell而言，使用的公式是:

```javascript
t[0] = m[0]
t[i + 1] = t[i] * (1 - factor) + factor * m[i]
```

这是一个递推式，. 这里t表示加权移动值，m是上面讲的metric异常程度，factor
是一个小于1的正小数。

这个式子会把旧数据稀释，新数据对结果的贡献更大（可以试着展开来验证），也就是说这个递推式计算出来的
移动平均值具有时效性，而且factor越大，时效性越好。

这个移动平均值更多地跟随最近的数据的变化趋势，因此可以把移动平均值拿来当做trending的排名参考量。

因此，我们采用加权移动平均值的办法，可以对每个metric仅仅维护一个数字来表达它目前的trending排名。把这些trending
排名放在一个zset里管理的话， 查询的时候，只要一次查询即可，还不用排序(zset自己就排好了)。

EOF
