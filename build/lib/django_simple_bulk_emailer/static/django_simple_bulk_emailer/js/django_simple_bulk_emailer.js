// Desktop-mobile CSS change:
function emailerDesktopMobileSwitch() {
    let windowWidth = document.body.clientWidth;
    const changeables = Array.from(
        document.querySelectorAll('.emailer_image')
    );

    if (windowWidth >= 720) {
        changeables.forEach(element => element.classList.remove('mobile'));
    } else {
        changeables.forEach(element => element.classList.add('mobile'));
    }
}


// Fire when page loads:
emailerDesktopMobileSwitch();


// Change on window resize:
window.addEventListener('resize', () => {
    emailerDesktopMobileSwitch();
});
