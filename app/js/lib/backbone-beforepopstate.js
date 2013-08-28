/*!
 * backbone-beforepopstate v1.0.0
 * https://github.com/veracross/backbone-beforepopstate
 *
 * Requires jQuery (1.7-1.9) and Backbone.js 1.0
 *
 * Copyright 2012-2013 Will Bond, Breuer & Co LLC <wbond@breuer.com>
 * Released under the MIT license
 *
 * Date: 2013-05-22
 */
Backbone.addBeforePopState = function(BB) {

  // Replaces the original checkUrl with one that runs beforepopstate event
  // handlers before the state is popped, allowing for equivalent functionality
  // to beforeunload handlers.
  BB.History.prototype._originalCheckUrl = BB.History.prototype.checkUrl;

  BB.History.prototype.checkUrl = function(e) {
    var confirmText, returnTo, fragment, e;
    var confirmSuffix = "\n\nAre you sure you want to leave this page?";

    // If there are beforepopstate handlers, continue as normal
    var events = jQuery(window).data('events') || jQuery._data(jQuery(window)[0], 'events');
    if (!events || !events.beforepopstate || BB.history._pushHistory.length == 0) {
      return BB.history._originalCheckUrl(e);
    }

    // Try each beforepopstate handler, retrieving the text
    // and then checking with the user
    var cancelled = false;
    for (var i = 0; i < events.beforepopstate.length; i++) {
      e= {
        type: "beforepopstate",
        fragment: BB.history._pushHistory[BB.history._pushHistory.length - 1]
      };
      confirmText = events.beforepopstate[i].handler(e);
      if (confirmText && !confirm(confirmText + confirmSuffix)) {
        cancelled = true;
        break;
      }
    }

    if (!cancelled) {
      BB.history._pushHistory.pop();
      return BB.history._originalCheckUrl(e);
    }

    // If the user did cancel, we have to push the previous URL
    // back onto the history to make it seem as if they never
    // moved anywhere.
    BB.history._popCancelled = true
    returnTo = BB.history.fragment;
    BB.history.fragment = BB.history.getFragment();
    BB.history._originalNavigate(returnTo);
  };


  // Replaces the original navigate with one that runs
  // beforepushstate event handlers before the state is
  // changed, allowing for equivalent functionality to
  // beforeunload handlers.
  BB.History.prototype._originalNavigate = BB.History.prototype.navigate;

  BB.History.prototype.navigate = function(fragment, options) {
    if (!BB.History.started) return false;

    var confirmText, e;
    var confirmSuffix = "\n\nAre you sure you want to leave this page?";

    // If there are beforepushstate handlers, continue as normal
    var events = jQuery(window).data('events') || jQuery._data(jQuery(window)[0], 'events');
    var cancelled = false;
    if (events && events.beforepushstate && BB.history._pushHistory.length > 0) {
      // Try each beforepushstate handler, retrieving the text
      // and then checking with the user
      for (var i = 0; i < events.beforepushstate.length; i++) {
        e = {
          type: "beforepushstate",
          fragment: fragment
        };
        confirmText = events.beforepushstate[i].handler(e);
        if (confirmText && !confirm(confirmText + confirmSuffix)) {
          cancelled = true;
          break;
        }
      }
    }

    if (!cancelled) {
      return BB.history._triggerPushState(fragment, options);
    }
  };

  // Sets up pushstate events to be triggered when navigate is called
  BB.History.prototype._triggerPushState = function(fragment, options) {
    var oldFragment = window.location.pathname + window.location.search + window.location.hash;
    BB.history._pushHistory.push(oldFragment);
    // Make sure the history doesn't get "wicked" big
    if (BB.history._pushHistory.length > 1000) {
      BB.history._pushHistory.shift();
    }

    var events, cont, i, e;
    result = BB.history._originalNavigate(fragment, options);

    events = jQuery(window).data('events') || jQuery._data(jQuery(window)[0], 'events');
    if (events && events.pushstate) {
      e = {
        bubbles: false,
        cancelable: true,
        preventDefault: function() {},
        srcElement: window,
        stopPropagation: function() {},
        target: window,
        type: "pushstate"
      };

      for (i = 0; i < events.pushstate.length; i++) {
        e.fragment = fragment;
        cont = events.pushstate[i].handler(e);
        // If the handler returns false, skip remaining handlers
        if (cont === false) {
          break;
        }
      }
    }

    return result;
  };

  // Adds an event handler that adds the fragment being popped to onto the event
  BB.History.prototype._originalStart = BB.History.prototype.start;
  BB.History.prototype.start = function(options) {
    BB.history._pushHistory = [];
    BB.history._popCancelled = false;
    var history = BB.history;

    // Adds a "fragment" property to popstate events so that they are like
    // pushstate, onbeforepushstate and onbeforepopstate. The fragment will be
    // set to false for the initial popstate event that chrome and safari trigger
    // when first loading a page.
    jQuery(window).on('popstate', function(e) {
      var fragment = history._pushHistory[history._pushHistory.length - 1];
      // The state is null for the default popstate event that chrome and safari
      // trigger on page load
      if (fragment === undefined && e.originalEvent.state === null) {
        fragment = false;
      }
      e.fragment = fragment;
    });

    BB.history._originalStart(options);

    // This prevents the popstate event handler from calling any handlers after
    // the one that backbone uses to fire navigation
    jQuery(window).on('popstate', function(e) {
      if (history._popCancelled) {
        e.stopImmediatePropagation();
        e.stopPropagation();
        e.preventDefault();
        history._popCancelled = false;
      }
    });
  };

  BB._originalDefaultHistory = BB.history;
  BB.history = new BB.History;
};
