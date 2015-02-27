// Yith Library Server is a password storage server.
// Copyright (C) 2015 Lorenzo Gil Sanchez <lorenzo.gil.sanchez@gmail.com>
//
// This file is part of Yith Library Server.
//
// Yith Library Server is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Yith Library Server is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with Yith Library Server.  If not, see <http://www.gnu.org/licenses/>.

(function ($, YITH) {
    "use strict";

    $(document).ready(function () {

	// Show the form for choosing to be tracked or not
	$('.google-analytics-preference-form').googleAnalyticsPreferenceForm(YITH.ga);
	// Enable GA if required
	$.fn.googleAnalyticsPreferenceForm.show(YITH.ga);

	// Custom jquery plugins
	$('.banner').banner();

	$('.check-all').checkAll();

	$('.confirm-form').confirmForm();

	$('.btn-email-verification').emailVerificationButton();

	$('.wizard').wizard();

	$.persona(YITH.persona);

	// Allow to close the popovers
	$("[rel=popover]").popover({trigger: 'hover'}).click(function (event) {
            event.preventDefault();
        });
        $("[rel=tooltip]").tooltip().click(function (event) {
            event.preventDefault();
        });
    });

}(jQuery, YITH));
