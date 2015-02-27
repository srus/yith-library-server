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

    var getSearchParam = function (param) {
        var items = window.location.search.substr(1).split("&"),
            index = 0,
            item = [];
        for (index = 0; index < items.length; index++) {
            item = items[index].split("=");
            if (item[0] === param) {
                return decodeURIComponent(item[1]);
            }
        }
        return null;
    };

    $.persona = function (options) {
        var currentUser = options.currentUser,
            currentProvider = options.currentProvider;

        if (!currentUser || currentProvider !== 'persona') {
            currentUser = null;
        }

        if (getSearchParam('force-persona-logout') === "true") {
            navigator.id.logout();
        }

        if (options.loginSelector) {
            $(options.loginSelector).click(function (event) {
                event.preventDefault();
                navigator.id.request();
            });
        }

        if (options.logoutSelector) {
            $(options.logoutSelector).click(function (event) {
                if (currentProvider === 'persona') {
                    event.preventDefault();
                    navigator.id.logout();
                }
            });
        }

        navigator.id.watch({
            loggedInUser: currentUser,
            onlogin: function (assertion) {
                var form = [
                    "<form class='hide' ",
                    "action='" + options.loginUrl + "' ",
                    "method='post'>",
                    "<input type='hidden' name='assertion' ",
                    "value='" + assertion + "'/>",
                    (options.nextUrl ? "<input type='hidden' name='next_url' value='" + decodeURIComponent(options.nextUrl) + "' />" : ""),
                    "</form>"
                ].join("");
                $(form).appendTo("body").submit();
            },
            onlogout: function () {
                if (currentProvider === 'persona') {
                    window.location = options.logoutUrl;
                }
            }
        });

    };

}(jQuery));
