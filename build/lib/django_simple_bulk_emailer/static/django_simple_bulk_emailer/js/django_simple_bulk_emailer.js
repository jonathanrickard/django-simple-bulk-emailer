// Desktop-mobile CSS change:
var emailerDesktopMobileSwitch = function() {
    var windowWidth = document.body.clientWidth;


    if (windowWidth >= 720) {
        $('.emailer_content')
			.add('.emailer_image')
				.removeClass('mobile');
    }

    else {
        $('.emailer_content')
			.add('.emailer_image')
				.addClass('mobile');
    }
}

// Fire when page loads:
emailerDesktopMobileSwitch();

// Change on window resize:
$(window).resize(function() {
    emailerDesktopMobileSwitch();
});
