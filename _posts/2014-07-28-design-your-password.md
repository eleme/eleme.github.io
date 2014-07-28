---
layout: post
title: 密码是件大事
date: 2014-07-28 20:50
author: lepture
categories: tech
---

互联网从来就不是安全的，到处是陷阱是危险。用户的账户也从来就不是安全的，你完全无法想像有多少人是用 123456 作为密码的。即使是 [GitHub](https://github.com/) 的程序员用户们，也有[不少人在使用弱密码](https://github.com/blog/1698-weak-passwords-brute-forced)。

一个正常的靠谱的网站不会存储用户的明文密码，它会使用加密（不可逆）方法存储加密后的内容，这样即使数据泄露（而这是常有的事）用户的密码也不会暴露。然而假使用户的密码是 123456 这样的弱密码，数据泄露与否也就无关紧要了，反正迟早都会被盗。我们不能信任用户的任何输入，即使是他自己的密码。

## 密码强度校验

Mark Burnett 是账户安全方面的专家，他曾总结过[一万个最常用的密码](https://xato.net/passwords/more-top-worst-passwords/)，排在第一的居然是 `password`。中国的情况略有不同，就我个人经验看来，排第一的应该是 `123456`。

你看，用户的密码是多么的不靠谱。既然用户自己不懂得保护自己，一个负责任的网站就应该帮助用户意识到他的密码是多么地不靠谱。这正是我前些天写作 [Safe](https://github.com/lepture/safe) 库的缘由。这是一个 Python 库，如果你的服务是用 Python 作为后端语言的，强烈建议你使用 Safe 来判断用户密码强度。另外还有一个 JavaScript 的版本，适用于前端与 Node.js 的 [Safe.js](http://lab.lepture.com/safe.js/)。

Safe 的密码强度校验分下面几步：

1. 长度校验，密码太短，排列组合不多，容易被破解。
2. 密码是否有一个模式，比如键盘上连在一起的 qwerty，比如有规律相间的 acegik。
3. 是否在一万个最常用的密码中，虽然有部分密码已经在前两条就不通过。

一个网站仅应该限制最短密码长度，即使用户的密码有 100 位也没有关系。上面已经提过靠谱的网站存储的是加密过的密文，通常它会是固定长度的，不会因为用户密码的长度而改变，限制用户密码的长度是没有道理的。一个网站也不应该限制密码的字符，比如不允许你使用某些特定的标点符号，因为网站存储的是加密过的密文，用户输入的特殊字符最终都会转换掉的。当你注册时，如果发现一个网站限制了最大密码长度，或者不允许你输入某些字符时，你就应该小心了，因为它很有可能是明文存储的密码。

## 旧算法的升级

靠谱的网站存储的是加密过的密文。但是有时候，原先的加密算法没设计好，比如只是简单的 `md5(password)`，你就应该升级一下加密算法了。推荐一下我通常使用的加密方案：

```
user.password = algorithm(site_secret + salt + raw_password)
```

升级是一件痛苦的事情，你不知道用户的明文密码，不能一下子全切换到新的算法上来。新注册的用户可以使用新的算法生成密码密文，但是老密码就没有办法了。你仍然需要想办法将老密文更新成新密文，最好的时机便是用户登录时。

```python
def login(user, password):
    if user.is_old_password and user.verify_password(password):
        user.is_old_password = False
        user.password = generate_new_password(password)
        user.save()
        return True
    # do other things
```

你等上半年便可去掉这段代码了。如果一个用户有半年时间都没有登录你的网站，你可以假设他忘记密码了，引导他去找回密码，在找回密码时使用新的算法生成新的密文。

## 二次认证

二次认证（两步认证）是一个更好的保护方案，当用户登录时填一个手机短信收取或者手机应用生成的验证码，只有验证码匹配时才认为是本人登录。二次认证通常使用 [TOTP](http://tools.ietf.org/html/rfc6238) 算法，例如 Google、Dropbox、GitHub 都是。如果你的网站保存有用户的私密信息，如果你的网站与金钱有关，二次认证是一个不错的选择。

这里有一个 Python 版的 HOTP/TOTP 库：[otpauth](https://github.com/lepture/otpauth)，你可以参考一下。作为一个用户，你应该[为你的所有敏感账户开启两步验证](http://chloerei.com/2013/11/20/enable-two-factor-authentication-for-all-your-sensitive-accounts/)。

## HTTPS

上面说了许多，但是假如用户登录系统使用的是 HTTP 而不是 HTTPS 传输的，一切都是徒劳。我能理解个人网站懒得用 HTTPS，但是一个公司，一个用户量巨大的网站，用户登录系统居然不是 HTTPS，简直就是耍流氓。

* [知乎为什么登录都不用 HTTPS ？](http://www.zhihu.com/question/21956033)
* [新浪微博登录为什么不使用HTTPS？](http://www.zhihu.com/question/20884913)

答案只有一个，他们不是负责任的网站。没有 HTTPS，你的密码再复杂，不一样能被轻易劫持！登录使用 HTTPS 是一个最基本的要求。
