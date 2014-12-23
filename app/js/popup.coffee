$(->
  showPopup = (html) ->
    el = $(html)

    htmlEl = $('html')
    htmlEl.addClass('popup')

    # Handle any change in the right-hand side of the page by changing the
    # HTML tag margin-right to make up for the
    oldMarginRight = htmlEl.css('margin-right')
    oldOverflowY = htmlEl.css('overflow-y')
    oldOverflowX = htmlEl.css('overflow-x')
    oldOverflow = htmlEl.css('overflow')
    scrollbarWidth = window.innerWidth - htmlEl[0].offsetWidth
    if scrollbarWidth > 0
      htmlEl.css({
        overflow: 'hidden',
        marginRight: scrollbarWidth + 'px'
      })

    el.css('opacity', '0.0')
    $('body').append(el)

    dialog = el.find('div.popup-dialog')
    iframe = el.find('iframe')
    content = el.find('div.popup-content')
    img = el.find('img')
    title = el.find('div.title')
    numEl = title.find('span.num')
    altEl = title.find('span.alt')

    resizable = null
    contentHeight = null
    calcContentHeight = ->
      if not contentHeight
        if iframe.length > 0
          resizable = iframe
          contentHeight = iframe[0].contentWindow.document.body.scrollHeight
        else if content.length > 0
          resizable = content
          contentHeight = content[0].offsetHeight
        else
          resizable = img
          contentHeight = img[0].height
      return contentHeight

    calcMaxHeight = ->
      return window.innerHeight - 100

    adjustSize = ->
      el.css('opacity', '1.0')
      maxHeight = calcMaxHeight()
      elHeight = calcContentHeight()

      if elHeight > maxHeight
        newHeight = maxHeight
      else
        newHeight = elHeight

      if img.length > 0
        resizable.css('max-height', newHeight)
        resizable.css('max-width', window.innerWidth - 300)
        dialog.css('width', resizable.width())
        dialog.css('max-width', 'none')
      else
        resizable.css('height', newHeight)

      el.toggleClass('filled', elHeight > maxHeight - 120)

    swapImage = (num, src, alt) ->
      img.attr('src', src)
      img.attr('alt', alt)
      if altEl.length > 0
        numEl.text(num)
        altEl.text(alt)
      else
        title.text(alt)
      contentHeight = null
      adjustSize()

    closePopup = ->
      if iframe.length > 0
        iframe.off('load', adjustSize)
      else if img.length > 0
        img.off('load', adjustSize)
      $(window).off('resize', adjustSize)
      el.css('opacity', '0.0')
      keymaster.unbind('esc,left,right')
      cleanUp = ->
        htmlEl.removeClass('popup')
        htmlEl.removeAttr('style')
        el.remove()
      setTimeout(cleanUp, 150)

    if iframe.length > 0
      iframe.on('load', adjustSize)
    else if img.length > 0
      img.on('load', adjustSize)
    else
      adjustSize()
    $(window).on('resize', adjustSize)

    keymaster('esc', closePopup)

    el.on('click', 'a.close, div.popup-scroller, div.popup-positioner', (e) ->
      target = $(e.target)

      # Don't close the popup if a click is on content in the dialog. This
      # allows for users to select content.
      if target.closest('div.popup-content').length > 0
        # For links in the popup, open them in a new window so we don't
        # accidentally close the popup and lose a user's unsaved content.
        if target.is('a')
          href = target.attr('href')
          if href != '#'
            window.open(href)
            e.preventDefault()

        return e.stopPropagation()

      e.preventDefault()
      closePopup()
    )

    return {
      el: el,
      adjustSize: adjustSize,
      swapImage: swapImage
    }

  isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)

  window.App.popup = (selector, delegate) ->
    if isMobile
      return

    handler = (e) ->
      target = $(e.target)
      href = target.attr('href')
      ext = href.toLowerCase().replace(/^.*\.([^.]+)$/, '$1')

      if ext in ['gif', 'jpg', 'jpeg', 'png']
        html = Handlebars.partials['popup-image']({
          src: href,
          alt: target.attr('alt')
        })
        showPopup(html)
        e.preventDefault()

    if delegate
      $(selector).on('click', delegate, handler)
    else
      $(selector).on('click', handler)

  window.App.popupGallery = (selector, delegate) ->
    if isMobile
      return

    handler = (e) ->
      e.preventDefault()
      img = $(e.target)
      link = img.closest('a')
      parent = $(e.delegateTarget)
      num = parent.find(delegate).index(link) + 1
      html = Handlebars.partials['popup-gallery']({
        num: num
        src: link.attr('href'),
        alt: img.attr('alt')
      })
      res = showPopup(html)
      el = res.el

      getChildren = () ->
        children = parent.find(delegate)
        current = children.filter('[href="' + el.find('img').attr('src') + '"]')
        index = children.index(current)
        return [children, index]

      updateImg = (children, index) ->
        newEl = children.eq(index)
        res.swapImage(
          index + 1,
          newEl.attr('href'),
          newEl.find('img').attr('alt')
        )

      moveNext = (e) ->
        [children, index] = getChildren()
        next = index + 1
        if next == children.length
          next = 0
        updateImg(children, next)
        e.preventDefault()
        e.stopPropagation()

      movePrevious = (e) ->
        [children, index] = getChildren()
        previous = index - 1
        if previous == -1
          previous = children.length - 1
        updateImg(children, previous)
        e.preventDefault()
        e.stopPropagation()

      el.on('click', 'a.next, img', moveNext)
      keymaster('right', moveNext)
      el.on('click', 'a.previous', movePrevious)
      keymaster('left', movePrevious)

    $(selector).on('click', delegate, handler)
)
