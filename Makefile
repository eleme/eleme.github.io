assets:
	@cat _assets/yue.css > static/vendor.css
	@cat _assets/fonts.css >> static/vendor.css
	@cat _assets/pygments.css >> static/vendor.css
	@cleancss static/vendor.css --s0 -o static/vendor.css

clean:
	@rm -fr _site

watch:
	@jekyll serve --watch
