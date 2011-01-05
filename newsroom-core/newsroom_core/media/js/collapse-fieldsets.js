$(function() {
	var show_text = 'show &darr;'
	var hide_text = 'hide &uarr;'
	var legends = $('fieldset.collapse legend')
	legends.parent().css('position', 'relative')
	legends.each(function() {
		$(this).nextAll().wrapAll('<div class="collapsable"></div>')
		var hider= $('<div class="collapse" style="float:right;position:absolute;right:2em;padding:0 .5em;background:#fff;top:-1.8em;cursor:pointer;">' + hide_text + '</div>')
		hider.hover(function(){
			$(this).addClass('collapse-hover')
		}, function() {
			$(this).removeClass('collapse-hover')
		})
		hider.toggle(function() {
			$(this).html(show_text)
			$(this).next('.collapsable').slideUp()
		}, function() {
			$(this).html(hide_text)
			$(this).next('.collapsable').slideDown()
		})
		$(this).after(hider)
	})
})