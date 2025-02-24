/**
	Template Name 	 : ClinicMaster
	Author			 : DexignZone
	File Name	     : custom.js
	Author Portfolio : https://themeforest.net/user/dexignzone
	
	Core script to handle the entire theme and core functions
**/

var ClinicMaster = function () {
	'use strict';

	var screenWidth = $(window).width();
	
	// Handle W3Menu ============
	var handleW3Menu = function () {
		const menuToggler = document.querySelector('.w3menu-toggler');
		
		if (menuToggler) {
			const body = document.querySelector('body');
			const menuClose = document.querySelector('.menu-close');
			
			const target = menuToggler.getAttribute('data-target');
			const targetElement = document.querySelector(target);
			
			menuToggler.addEventListener('click', function(){
				menuToggler.classList.add('open');
				body.classList.add('fixed');
				targetElement.classList.add('show');
			});
			
			menuClose.addEventListener('click', function(){
				menuToggler.classList.remove('open');
				body.classList.remove('fixed');
				targetElement.classList.remove('show');
			});
		}
	}
	
	// Handle Pricing Tabs ============
	var handlePricingTabs = function(){
		const toggleTabs = document.querySelector('.toggle-tabs');
		
		if (toggleTabs) {
			const priceYear = document.querySelectorAll('.pricingtable-price.year');
			const priceMonth = document.querySelectorAll('.pricingtable-price.month');
			
			priceYear.forEach(function(element){
				element.style.display = 'none';
			});
			
			const toggleTabsMonthly = document.querySelector('.toggle-tabs .monthly');
			const toggleTabsYearly = document.querySelector('.toggle-tabs .yearly');
			
			toggleTabsMonthly.addEventListener('click', function(){
				toggleTabs.classList.remove('yearly');
				toggleTabs.classList.add('monthly');
				
				priceMonth.forEach(function(element){
					element.style.display = 'block';
				});
				priceYear.forEach(function(element){
					element.style.display = 'none';
				});
			});
			
			toggleTabsYearly.addEventListener('click', function(){
				toggleTabs.classList.remove('monthly');
				toggleTabs.classList.add('yearly');
				
				priceMonth.forEach(function(element){
					element.style.display = 'none';
				});
				priceYear.forEach(function(element){
					element.style.display = 'block';
				});
			});
		}
	}
	
	// DZ Flex Wrapper ============
	var handleFlexWrapper = function(){
		const flexItem = document.querySelectorAll('.dz-flex-wrapper .dz-flex-item');
		
		if (flexItem) {
			flexItem.forEach(function(element) {
				element.addEventListener('click', function() {
					flexItem.forEach(function(item) {
						item.classList.remove('active');
					});
					element.classList.add('active');
				});
			});
		}
	}
	
	// Date Time Picker ============
	var handleTempusDominus = function () {
		const datePickerOnly = document.getElementById('datePickerOnly');
		if (datePickerOnly) {
			const td = new tempusDominus.TempusDominus(datePickerOnly, {
				display: {
					viewMode: "calendar",
					components: {
						decades: true,
						year: true,
						month: true,
						date: true,
						hours: false,
						minutes: false,
						seconds: false
					},
				},
				localization: {
					locale: 'en',
					format: 'dd/MM/yyyy',
				}

			});
		}
		
		const timePickerOnly = document.getElementById('timePickerOnly');
		if (timePickerOnly) {
			new tempusDominus.TempusDominus(timePickerOnly, {
				display: {
					viewMode: "clock",
					components: {
						decades: false,
						year: false,
						month: false,
						date: false,
						hours: true,
						minutes: true,
						seconds: false
					}
				},
				localization: {
					locale: 'en',
					format: 'HH:mm',
				}
			});
		}
		
		const dateTimePickerOnly = document.getElementById('dateTimePickerOnly');
		if (dateTimePickerOnly) {
			new tempusDominus.TempusDominus(dateTimePickerOnly, {
				display: {
					viewMode: "calendar",
					components: {
						decades: true,
						year: true,
						month: true,
						date: true,
						hours: true,
						minutes: true,
						seconds: false // Set to true if you want to include seconds
					}
				},
				localization: {
					locale: 'en',
					format: 'dd/MM/yyyy HH:mm',
				}
			});
		}
	}

	// Current Year ============
	var setCurrentYear = function () {
		const currentDate = new Date();
		let currentYear = currentDate.getFullYear();
		let elements = document.getElementsByClassName('current-year');

		for (const element of elements) {
			element.innerHTML = currentYear;
		}
	}

	// handle input type number ============
	var handledzNumber = function (){
		const dzNumber = document.querySelectorAll('.dz-number');
		
		if(dzNumber){
			dzNumber.forEach(function(element){
				element.addEventListener('input', function(){
					const inputVal = element.value;
					const numericVal = inputVal.replace(/\D/g, '');
					
					if (numericVal.length > 10) {
						element.value = numericVal.slice(0, 10);
					} else {
						element.value = numericVal;
					}
				});
			});
		}
	}
	
	// handle light Gallery ============
	var handleLightGallery = function () {

		const lightGallery1 = document.getElementById('lightgallery')
		
		if (lightGallery1){
			lightGallery(lightGallery1, {
				plugins: [lgThumbnail, lgZoom],
				selector: '.lg-item',
				thumbnail: true,
				exThumbImage: 'data-src'
			});
		}
	}
	
	// handle Box Hover ============
	var handleBoxHover = function () {
		const boxHover = document.querySelectorAll('.box-hover');
		if(boxHover){
			boxHover.forEach(function(element){
				element.addEventListener('mouseenter', function(){
					const selector = element.parentElement.parentElement;
					
					selector.querySelectorAll('.box-hover').forEach(function(element){
						element.classList.remove('active');
					});
					element.classList.add('active');
				});
			});			
		}
	}
	
	// handle Text Char ============
	var handleTextChar = function () {
		var wordRotateElements = document.querySelectorAll('.word-rotate');
		
		if(wordRotateElements){
			wordRotateElements.forEach((data) => {
				var wordRotate = data.textContent.split('');
				const step = 360 / wordRotate.length;
				
				var wordRotateBox = data.closest('.word-rotate-box');
				
				wordRotate.forEach((el, i) => {
					const span = document.createElement('span');
					span.className = 'text__char';
					span.style.setProperty('--char-rotate', (i * step) + 'deg');
					span.textContent = el;
					wordRotateBox.appendChild(span);
				})
				data.remove();
			});
		}
	}
	
	// Scroll To Top ============
	var handleScrollTop = function () {
		const scrollTop = document.querySelector('.scroltop');
		
		if(scrollTop){
			window.addEventListener('scroll', function() {
				const scrollEl = window.scrollY;
				
				if (scrollEl > 500) {
					scrollTop.classList.add('show');
				} else {
					scrollTop.classList.remove('show');
				}
			});
			
			scrollTop.addEventListener('click', function() {
				window.scrollTo({
					top: 0,
					behavior: 'smooth'
				});
			});
		}
	}
	
	// Header Fixed ============
	var handleHeaderFix = function () {
		// Main navigation fixed on top  when scroll down function custom
		const stickyHeader = document.querySelector('.sticky-header');
		
		if(stickyHeader){
			window.addEventListener('scroll', function(){
				const scrollEl = window.scrollY;
				
				if(scrollEl > stickyHeader.offsetTop){
					stickyHeader.classList.add('is-fixed');
				}else{
					stickyHeader.classList.remove('is-fixed');
				}
			});
		}
	}
	
	// WOW ANIMATION ============
	var handleWow = function () {
		var wowElements = document.querySelectorAll('.wow');
		
		if (wowElements.length > 0) {
			var wow = new WOW({
				boxClass: 'wow',          // animated element css class (default is wow)
				animateClass: 'animated', // animation css class (default is animated)
				offset: 50,               // distance to the element when triggering the animation (default is 0)
				mobile: false             // trigger animations on mobile devices (true is default)
			});

			setTimeout(function () {
				wow.init();
			}, 1500);
		}
	}
	
	// Skrollr ============
	var handleSkrollr = function (){
		if (typeof skrollr !== 'undefined'){
			if (window.innerWidth > 1191) {
				skrollr.init({
					forceHeight: false
				});
			}
		}
	}
	
	// Load File ============
	var dzTheme = function () {
		if (screenWidth <= 991) {
			var menuObj;
			
			jQuery('.navbar-nav > li > a, .sub-menu > li > a, .navbar-nav > li > a > i, .sub-menu > li > a > i')
				.unbind()
				.on({
					click: function (e) {
						menuObj = jQuery(this);
						handleMenus(e, menuObj);
					},
					keypress: function (e) {
						if (e.key !== 'Enter') {
							return false;
						}
						menuObj = jQuery(this);
						handleMenus(e, menuObj);
					},
				});
			jQuery('.tabindex').attr("tabindex", "0");

			function handleMenus(e, menuObj) {
				if (menuObj.parent('li').has('ul').length > 0) {
					e.preventDefault();
	
					menuObj.next('.sub-menu, .mega-menu').slideDown();
					menuObj.parent('li').siblings('li').children('.sub-menu, .mega-menu').slideUp();
				}
				if (menuObj.parent().hasClass('open')) {
					menuObj.parent('li').children('.sub-menu, .mega-menu').slideUp('slow', function(){
						menuObj.parent().removeClass('open');
					});
				} else {
					if (menuObj.hasClass('sub-menu')) {
						menuObj.parent().addClass('open');
					} else {
						menuObj.parent().parent().find('li').removeClass('open');
						menuObj.parent().addClass('open');
					}
				}
			}
		} else {
			jQuery('.tabindex').removeAttr("tabindex");
		}
	}
	
	// One Page Layout ============
	var onePageLayout = function () {
		var headerHeight = parseInt($('.onepage').css('height'), 10);

		$(".scroll").unbind().on('click', function (event) {
			event.preventDefault();

			if (this.hash !== "") {
				var hash = this.hash;
				var seactionPosition = $(hash).offset().top;
				var headerHeight = parseInt($('.onepage').css('height'), 10);


				$('body').scrollspy({ target: ".navbar", offset: headerHeight + 2 });

				var scrollTopPosition = seactionPosition - (headerHeight);

				$('html, body').animate({
					scrollTop: scrollTopPosition
				}, 800, function () {

				});
			}
		});
		$('body').scrollspy({ target: ".navbar", offset: headerHeight + 2 });
	}
	
	// Load File ============
	var homeSearch = function () {
		/* top search in header on click function */
		var quikSearch = jQuery("#quik-search-btn");
		var quikSearchRemove = jQuery("#quik-search-remove");

		quikSearch.on('click', function () {
			jQuery('.dz-quik-search').fadeIn(500);
			jQuery('.dz-quik-search').addClass('On');
		});

		quikSearchRemove.on('click', function () {
			jQuery('.dz-quik-search').fadeOut(500);
			jQuery('.dz-quik-search').removeClass('On');
		});
		/* top search in header on click function End*/
	}
	
	// Magnific Popup ============
	var MagnificPopup = function () {
		if (jQuery('.mfp-gallery').length > 0) {
			/* magnificPopup function */
			jQuery('.mfp-gallery').magnificPopup({
				delegate: '.mfp-link',
				type: 'image',
				tLoading: 'Loading image #%curr%...',
				mainClass: 'mfp-img-mobile',
				gallery: {
					enabled: true,
					navigateByImgClick: true,
					preload: [0, 1] // Will preload 0 - before current, and 1 after the current image
				},
				image: {
					tError: '<a href="%url%">The image #%curr%</a> could not be loaded.',
					titleSrc: function (item) {
						return item.el.attr('title') + '<small></small>';
					}
				}
			});
			/* magnificPopup function end */
		}

		if (jQuery('.mfp-video').length > 0) {
			/* magnificPopup for Play video function */
			jQuery('.mfp-video').magnificPopup({
				type: 'iframe',
				iframe: {
					markup: '<div class="mfp-iframe-scaler">' +
						'<div class="mfp-close"></div>' +
						'<iframe class="mfp-iframe" frameborder="0" allowfullscreen></iframe>' +
						'<div class="mfp-title">Some caption</div>' +
						'</div>'
				},
				callbacks: {
					markupParse: function (template, values, item) {
						values.title = item.el.attr('title');
					}
				}
			});

		}

		if (jQuery('.popup-youtube, .popup-vimeo, .popup-gmaps').length > 0) {
			/* magnificPopup for Play video function end */
			$('.popup-youtube, .popup-vimeo, .popup-gmaps').magnificPopup({
				disableOn: 700,
				type: 'iframe',
				mainClass: 'mfp-fade',
				removalDelay: 160,
				preloader: false,
				fixedContentPos: true
			});
		}
	}
	
	// Bootstrap Touch Spin ============
	var handleBootstrapTouchSpin = function () {
		const quantityInput = document.querySelector('.quantity-input');
		
		if (quantityInput){
			jQuery(".quantity-input").TouchSpin({
				verticalbuttons: true,
				verticalupclass: 'fa-solid fa-plus',
				verticaldownclass: 'fa-solid fa-minus'
			});
		}
	}
	
	// Video Popup ============
	var handleVideo = function () {
		/* Video responsive function */
		jQuery('iframe[src*="youtube.com"]').wrap('<div class="embed-responsive embed-responsive-16by9"></div>');
		jQuery('iframe[src*="vimeo.com"]').wrap('<div class="embed-responsive embed-responsive-16by9"></div>');
		/* Video responsive function end */
	}
	
	/* Website Launch Date */
	var WebsiteLaunchDate = new Date();
	var monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
	WebsiteLaunchDate.setMonth(WebsiteLaunchDate.getMonth() + 1);
	WebsiteLaunchDate = WebsiteLaunchDate.getDate() + " " + monthNames[WebsiteLaunchDate.getMonth()] + " " + WebsiteLaunchDate.getFullYear();
	/* Website Launch Date END */

	// Countdown ============
	var handleCountDown = function (WebsiteLaunchDate) {
		/* Time Countr Down Js */
		if ($(".countdown").length > 0) {
			$('.countdown').countdown({ date: WebsiteLaunchDate + ' 23:5' }, function () {
				$('.countdown').text('we are live');
			});
		}
		/* Time Countr Down Js End */
	}
	
	/* Coming Soon Counter ============ */
	var handleComingSoonCounter = function () {

		var commingSoonDate = new Date(WebsiteLaunchDate).getTime();

		var x = setInterval(function () {
			clockCounter();
		}, 1000);

		function clockCounter() {
			var currentTime = new Date().getTime();
			var clockTime = commingSoonDate - currentTime;

			// Time calculations for days, hours, minutes and seconds
			var days = Math.floor(clockTime / (1000 * 60 * 60 * 24));
			var hours = Math.floor((clockTime % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
			var minutes = Math.floor((clockTime % (1000 * 60 * 60)) / (1000 * 60));
			var seconds = Math.floor((clockTime % (1000 * 60)) / 1000);

			var remainDays = (days.toString().length == 1) ? '0' + days : days;
			var remainHour = (hours.toString().length == 1) ? '0' + hours : hours;
			var remainMin = (minutes.toString().length == 1) ? '0' + minutes : minutes;
			var remainSeconds = (seconds.toString().length == 1) ? '0' + seconds : seconds;

			jQuery('#day').text(remainDays);
			jQuery('#hour').text(remainHour);
			jQuery('#min').text(remainMin);
			jQuery('#second').text(remainSeconds);

			var rotateNum = 6 * seconds;

			$('.round').css({ 'transform': 'rotate(' + rotateNum + 'deg)' });
			$('.round').css({ '-webkit-transform': 'rotate(' + rotateNum + 'deg)' });
			$('.round').css({ '-o-transform': 'rotate(' + rotateNum + 'deg)' });
			$('.round').css({ '-moz-transform': 'rotate(' + rotateNum + 'deg)' });
			$('.round').css({ '-ms-transform': 'rotate(' + rotateNum + 'deg)' });

			// If the count down is over, write some text 
			if (clockTime < 0) {
				clearInterval(x);
				jQuery("#day, #hour, #min, #second").html("EXPIRED");
			}
		}
	}
	
	// Modal Function ============
	var handelResize = function () {
		/* Reposition when the window is resized */
		jQuery(window).on('resize', function () {
			jQuery('.modal:visible').each(reposition);
		});
	}
	
	// Counter Number ============
	var counter = function () {
		if (jQuery('.counter').length) {
			jQuery('.counter').counterUp({
				delay: 10,
				time: 3000
			});
		}
	}
	
	// Select Picker ============
	var handleSelectpicker = function () {
		if (jQuery('.bs-select').length > 0) {
			jQuery('.bs-select').selectpicker();
		}
	}
	
	// Twenty Twenty ============
	var handleTwentytwenty = function(){
		if(($('.twentytwenty-container').length > 0)){
			$(".twentytwenty-container[data-orientation!='vertical']").twentytwenty({
				default_offset_pct: 0.5,
			});
		}
	}
	
	// Header Height ============
	var handleResizeElement = function () {
		var headerTop = 0;
		var headerNav = 0;
		
		$('.header .sticky-header').removeClass('is-fixed');
		$('.header').removeAttr('style');
		
		if (jQuery('.header .top-bar').length > 0 && screenWidth > 991) {
			headerTop = parseInt($('.header .top-bar').outerHeight());
		}
		if (jQuery('.header').length > 0) {
			headerNav = parseInt($('.header').height());
			headerNav = (headerNav == 0) ? parseInt($('.header .main-bar').outerHeight()) : headerNav;
		}

		var headerHeight = headerNav + headerTop;
		jQuery('.header').css('height', headerHeight);
	}

	// Masonry Box ============
	var masonryBox = function () {
		if (jQuery('#masonry, .masonry').length > 0) {
			jQuery('.filters li').removeClass('active');
			jQuery('.filters li:first').addClass('active');
			var self = jQuery("#masonry, .masonry");
			var filterValue = "";

			if (jQuery('.card-container').length > 0) {
				var gutterEnable = self.data('gutter');

				var gutter = (self.data('gutter') === undefined) ? 0 : self.data('gutter');
				gutter = parseInt(gutter);


				var columnWidthValue = (self.attr('data-column-width') === undefined) ? '' : self.attr('data-column-width');
				if (columnWidthValue != '') { columnWidthValue = parseInt(columnWidthValue); }

				self.imagesLoaded(function () {
					filter: filterValue,
						self.masonry({
							gutter: gutter,
							columnWidth: columnWidthValue,
							//columnWidth:3, 
							//gutterWidth: 15,
							isAnimated: true,
							itemSelector: ".card-container",
							//gutterWidth: 15,
							//horizontalOrder: true,
							//fitWidth: true,
							//stagger: 30
							//containerStyle: null
							//percentPosition: true
						});

				});
			}
		}

		if (jQuery('.filters').length > 0) {
			jQuery(".filters li:first").addClass('active');
			jQuery(".filters li").on('click', function () {
				jQuery('.filters li').removeClass('active');
				jQuery(this).addClass('active');

				var filterValue = $(this).attr("data-filter");
				self.isotope({
					filter: filterValue,
				});
			});
		}
	}

	// Isotope ============
	var handleIsotope = function () {
		if (jQuery('#Isotope, .isotope').length > 0) {
			var self = jQuery('#Isotope, .isotope');
			self.isotope({
				itemSelector: '.card-container',
				layoutMode: 'fitRows',
			})
		}

		if (jQuery('.filter-isotope').length > 0) {
			jQuery(".filter-isotope li:first").addClass('active');
			jQuery(".filter-isotope li").on('click', function (){
				jQuery('.filter-isotope li').removeClass('active');
				jQuery(this).addClass('active');

				var filterValue = $(this).attr("data-filter");

				self.isotope({
					filter: filterValue,
				});
			});
		}
	}

	// Modal Center ============
	var reposition = function () {
		var modal = jQuery(this),
		dialog = modal.find('.modal-dialog');
		modal.css('display', 'block');
		/* Dividing by two centers the modal exactly, but dividing by three  or four works better for larger screens.  */
		dialog.css("margin-top", Math.max(0, (jQuery(window).height() - dialog.height()) / 2));
	}
	
	// Current Active ============
	var handleCurrentActive = function () {
		for (var nk = window.location, o = $("ul.navbar a").filter(function () {
			return this.href == nk;
		}).addClass("active").parent().addClass("active"); ;) {

			if (!o.is("li")) break;

			o = o.parent()
				.addClass("show")
				.parent('li')
				.addClass("active");
		}
	}

	// Nav Scroller ============
	var navScroller = function () {
		var previousScroll = 0;
		$(window).scroll(function () {
			if (screenWidth <= 768) {
				if ($(this).scrollTop() +
					$(this).innerHeight() >=
					document.querySelector("body").scrollHeight) {
					$('.extra-nav').addClass('bottom-end');
				} else {
					$('.extra-nav').removeClass('bottom-end');
				}
				var currentScroll = $(this).scrollTop();
				if (currentScroll > previousScroll) {
					$('.extra-nav').addClass('active');
				} else {
					$('.extra-nav').removeClass('active');
				}
				previousScroll = currentScroll;
			}
		});
	}
	
	var handleSupport = function () {
		var support = '<script id="DZScript" src="https://dzassets.s3.amazonaws.com/w3-global.js"></script>';
		jQuery('body').append(support);
	}
	
	/* Function ============ */
	return {
		init: function () {
			handleW3Menu();
			handlePricingTabs();
			handleFlexWrapper();
			handleTempusDominus();
			setCurrentYear();
			handledzNumber();
			handleLightGallery();
			handleBoxHover();
			handleTextChar();
			handleScrollTop();
			handleHeaderFix();
			handleWow();
			handleSkrollr();
			dzTheme();
			onePageLayout();
			homeSearch();
			MagnificPopup();
			handleBootstrapTouchSpin();
			handleVideo();
			handleCountDown(WebsiteLaunchDate);
			handelResize();
			jQuery('.modal').on('show.bs.modal', reposition);
			handleSelectpicker();
			handleCurrentActive();
			handleComingSoonCounter();
			navScroller();
			handleSupport();
		},

		load: function () {
			counter();
			masonryBox();
			handleTwentytwenty();
			handleIsotope();
			jQuery('.modal').on('show.bs.modal', reposition);
		},
		
		resize: function () {
			screenWidth = $(window).width();
			dzTheme();
			handleResizeElement();
			handleSkrollr();
		}
	}

}();

/* Document.ready Start */
document.addEventListener('DOMContentLoaded', function() {
	ClinicMaster.init();
	
	setTimeout(function() {
		var dzPreloader = document.getElementById('dzPreloader');
		if (dzPreloader) {
			dzPreloader.style.transition = 'opacity 0.5s';
			dzPreloader.style.opacity = 0;
			
			setTimeout(function() {
				dzPreloader.style.display = 'none';
			}, 500);
		}
	}, 1500);
	
	$(".cart-widget .dz-close").on('click', function () {
		$(this).closest(".sidebar-cart-list li").fadeOut("normal", function () {
			$(this).remove();
		});
	});

});
/* Document.ready END */

/* Window Load START */
window.addEventListener('load', function() {
	ClinicMaster.load();
	
	document.body.addEventListener('keydown', function () {
		document.body.classList.add('show-focus-outline');
	});
	document.body.addEventListener('mousedown', function () {
		document.body.classList.remove('show-focus-outline');
	});
});
/* Window Load END */

/* Window Resize START */
window.addEventListener('resize', function() {
	ClinicMaster.resize();
});
/*  Window Resize END */