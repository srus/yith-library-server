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

    $.fn.emailVerificationButton = function (options) {
        return this.each(function () {            
            $(this).click(function (event) {
                var $button = $(this),
		    $modal = $button.parents('.modal'),
		    hideOnSuccess = $button.data('hide-on-success');

                event.preventDefault();

                if ($button.hasClass("disabled")) {
                    return;
                }
                $button.addClass("disabled");
                $.ajax({
                    type: 'POST',
                    url: $button.attr("href"),
                    data: {submit: 'Send verification code'},
                    dataType: 'json',
                    success: function (data, textStatus, jqXHR) {
                        if (data.status === 'ok') {
                            $modal.find(".alert-info").removeClass("hide");
			    $(hideOnSuccess).addClass("hide");
                        } else {
                            $modal.find(".alert-error").removeClass("hide").find("strong").text(data.error);
                            $modal.find(".alert-info").addClass("hide");
                            $button.removeClass("disabled");
                        }
                    }
                });
            });
        });
    };

}(jQuery));
