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

(function ($) {
    "use strict";

    var _gaq;

    if (window._gaq === undefined) {
        _gaq = window._gaq = [];
    }

    var addGoogleAnalyticsScript = function (code) {
        var ga = document.createElement('script'),
            script = document.getElementsByTagName('script')[0];

        _gaq.push(['_setAccount', code]);
        _gaq.push(['_trackPageview']);

        ga.type = 'text/javascript';
        ga.async = true;
        ga.src = ('https:' === document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
        script.parentNode.insertBefore(ga, script);
    };

    var GoogleAnalyticsForm = function (form, code) {
	this.form = form;
	this.code = code;
    };

    GoogleAnalyticsForm.prototype.sendPreference = function (allow) {
        var self = this, $form = $(this.form);
        $.ajax({
            type: $form.attr('method'),
            url: $form.attr('action'),
            data: allow,
            success: function (data) {
                $form.parent('.alert').slideUp();
                if (data.allow) {
		    addGoogleAnalyticsScript(self.code);
                }
            }
        });
    };

    $.fn.googleAnalyticsPreferenceForm = function (options) {
	return this.each(function () {
	    var gaf = new GoogleAnalyticsForm(this, options.code);
	    $(this)
	        .find('[name="yes"]').click(function (event) {
		    event.preventDefault();
		    gaf.sendPreference({'yes': $(this).val()});
		})
		.end()
		.find('[name="no"]').click(function (event) {
		    event.preventDefault();
		    gaf.sendPreference({'no': $(this).val()});
		});
	});
    };

    $.fn.googleAnalyticsPreferenceForm.show = function (options) {
	if (options.show) {
	    addGoogleAnalyticsScript(options.code);
	}
    };


}(jQuery));
