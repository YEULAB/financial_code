"""
A collection of functions for collecting, analyzing and plotting
financial data.   User contributions welcome!

This module is deprecated in 1.4 and will be moved to `mpl_toolkits`
or it's own project in the future.

"""
from __future__ import division, print_function
import contextlib
import os
import sys
import warnings
from urllib2 import urlopen

if sys.version_info[0] < 3:
    from hashlib import md5
else:
    import hashlib
    md5 = lambda x: hashlib.md5(x.encode())

import datetime

import numpy as np

from matplotlib import verbose, get_cachedir
from matplotlib.dates import date2num
from matplotlib.cbook import iterable, mkdirs
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.colors import colorConverter
from matplotlib.lines import Line2D, TICKLEFT, TICKRIGHT
from matplotlib.patches import Rectangle
from matplotlib.transforms import Affine2D

from matplotlib.cbook import mplDeprecation

cachedir = get_cachedir()
# cachedir will be None if there is no writable directory.
if cachedir is not None:
    cachedir = os.path.join(cachedir, 'finance.cache')
else:
    # Should only happen in a restricted environment (such as Google App
    # Engine). Deal with this gracefully by not caching finance data.
    cachedir = None


stock_dt_ohlc = np.dtype([('date', object),
                     ('year', np.int16),
                     ('month', np.int8),
                     ('day', np.int8),
                     ('d', np.float),     # mpl datenum
                     ('open', np.float),
                     ('high', np.float),
                     ('low', np.float),
                     ('close', np.float),
                     ('volume', np.float),
                     ('aclose', np.float)])


stock_dt_ochl = np.dtype([('date', object),
                     ('year', np.int16),
                     ('month', np.int8),
                     ('day', np.int8),
                     ('d', np.float),     # mpl datenum
                     ('open', np.float),
                     ('close', np.float),
                     ('high', np.float),
                     ('low', np.float),
                     ('volume', np.float),
                     ('aclose', np.float)])

_warn_str = ("This function has been deprecated in 1.4 in favor "
             "of `{fun}_ochl`, "
             "which maintains the original argument order, "
             "or `{fun}_ohlc`, "
             "which uses the open-high-low-close order. "
             "This function will be removed in 1.5")


def parse_yahoo_historical_ochl(fh, adjusted=True, asobject=False):
    """Parse the historical data in file handle fh from yahoo finance.

    Parameters
    ----------

    adjusted : bool
      If True (default) replace open, close, high, low prices with
      their adjusted values. The adjustment is by a scale factor, S =
      adjusted_close/close. Adjusted prices are actual prices
      multiplied by S.

      Volume is not adjusted as it is already backward split adjusted
      by Yahoo. If you want to compute dollars traded, multiply volume
      by the adjusted close, regardless of whether you choose adjusted
      = True|False.


    asobject : bool or None
      If False (default for compatibility with earlier versions)
      return a list of tuples containing

        d, open, close, high, low,  volume

      If None (preferred alternative to False), return
      a 2-D ndarray corresponding to the list of tuples.

      Otherwise return a numpy recarray with

        date, year, month, day, d, open, close, high, low,
        volume, adjusted_close

      where d is a floating poing representation of date,
      as returned by date2num, and date is a python standard
      library datetime.date instance.

      The name of this kwarg is a historical artifact.  Formerly,
      True returned a cbook Bunch
      holding 1-D ndarrays.  The behavior of a numpy recarray is
      very similar to the Bunch.

    """
    return _parse_yahoo_historical(fh, adjusted=adjusted, asobject=asobject,
                           ochl=True)


def parse_yahoo_historical_ohlc(fh, adjusted=True, asobject=False):
    """Parse the historical data in file handle fh from yahoo finance.

    Parameters
    ----------

    adjusted : bool
      If True (default) replace open, high, low, close prices with
      their adjusted values. The adjustment is by a scale factor, S =
      adjusted_close/close. Adjusted prices are actual prices
      multiplied by S.

      Volume is not adjusted as it is already backward split adjusted
      by Yahoo. If you want to compute dollars traded, multiply volume
      by the adjusted close, regardless of whether you choose adjusted
      = True|False.


    asobject : bool or None
      If False (default for compatibility with earlier versions)
      return a list of tuples containing

        d, open, high, low, close, volume

      If None (preferred alternative to False), return
      a 2-D ndarray corresponding to the list of tuples.

      Otherwise return a numpy recarray with

        date, year, month, day, d, open, high, low,  close,
        volume, adjusted_close

      where d is a floating poing representation of date,
      as returned by date2num, and date is a python standard
      library datetime.date instance.

      The name of this kwarg is a historical artifact.  Formerly,
      True returned a cbook Bunch
      holding 1-D ndarrays.  The behavior of a numpy recarray is
      very similar to the Bunch.
    """
    return _parse_yahoo_historical(fh, adjusted=adjusted, asobject=asobject,
                           ochl=False)


def parse_yahoo_historical(fh, adjusted=True, asobject=False):
    """Parse the historical data in file handle fh from yahoo finance.


    This function has been deprecated in 1.4 in favor of
    `parse_yahoo_historical_ochl`, which maintains the original argument
    order, or `parse_yahoo_historical_ohlc`, which uses the
    open-high-low-close order.  This function will be removed in 1.5


    Parameters
    ----------

    adjusted : bool
      If True (default) replace open, close, high, low prices with
      their adjusted values. The adjustment is by a scale factor, S =
      adjusted_close/close. Adjusted prices are actual prices
      multiplied by S.

      Volume is not adjusted as it is already backward split adjusted
      by Yahoo. If you want to compute dollars traded, multiply volume
      by the adjusted close, regardless of whether you choose adjusted
      = True|False.


    asobject : bool or None
      If False (default for compatibility with earlier versions)
      return a list of tuples containing

        d, open, close, high, low, volume

      If None (preferred alternative to False), return
      a 2-D ndarray corresponding to the list of tuples.

      Otherwise return a numpy recarray with

        date, year, month, day, d, open, close, high, low,
        volume, adjusted_close

      where d is a floating poing representation of date,
      as returned by date2num, and date is a python standard
      library datetime.date instance.

      The name of this kwarg is a historical artifact.  Formerly,
      True returned a cbook Bunch
      holding 1-D ndarrays.  The behavior of a numpy recarray is
      very similar to the Bunch.

    ochl : bool
        Temporary argument to select between ochl and ohlc ordering.
        Defaults to True to preserve original functionality.

    """

    warnings.warn(_warn_str.format(fun='parse_yahoo_historical'),
                  mplDeprecation)

    return _parse_yahoo_historical(fh, adjusted=adjusted, asobject=asobject,
                           ochl=True)


def _parse_yahoo_historical(fh, adjusted=True, asobject=False,
                           ochl=True):
    """Parse the historical data in file handle fh from yahoo finance.


    Parameters
    ----------

    adjusted : bool
      If True (default) replace open, high, low, close prices with
      their adjusted values. The adjustment is by a scale factor, S =
      adjusted_close/close. Adjusted prices are actual prices
      multiplied by S.

      Volume is not adjusted as it is already backward split adjusted
      by Yahoo. If you want to compute dollars traded, multiply volume
      by the adjusted close, regardless of whether you choose adjusted
      = True|False.


    asobject : bool or None
      If False (default for compatibility with earlier versions)
      return a list of tuples containing

        d, open, high, low, close, volume

       or

        d, open, close, high, low, volume

      depending on `ochl`

      If None (preferred alternative to False), return
      a 2-D ndarray corresponding to the list of tuples.

      Otherwise return a numpy recarray with

        date, year, month, day, d, open, high, low, close,
        volume, adjusted_close

      where d is a floating poing representation of date,
      as returned by date2num, and date is a python standard
      library datetime.date instance.

      The name of this kwarg is a historical artifact.  Formerly,
      True returned a cbook Bunch
      holding 1-D ndarrays.  The behavior of a numpy recarray is
      very similar to the Bunch.

    ochl : bool
        Selects between ochl and ohlc ordering.
        Defaults to True to preserve original functionality.

    """
    if ochl:
        stock_dt = stock_dt_ochl
    else:
        stock_dt = stock_dt_ohlc

    results = []

    #    datefmt = '%Y-%m-%d'
    fh.readline()  # discard heading
    for line in fh:

        vals = line.split(',')
        if len(vals) != 7:
            continue      # add warning?
        datestr = vals[0]
        #dt = datetime.date(*time.strptime(datestr, datefmt)[:3])
        # Using strptime doubles the runtime. With the present
        # format, we don't need it.
        dt = datetime.date(*[int(val) for val in datestr.split('-')])
        dnum = date2num(dt)
        open, high, low, close = [float(val) for val in vals[1:5]]
        volume = float(vals[5])
        aclose = float(vals[6])
        if ochl:
            results.append((dt, dt.year, dt.month, dt.day,
                            dnum, open, close, high, low, volume, aclose))

        else:
            results.append((dt, dt.year, dt.month, dt.day,
                            dnum, open, high, low, close, volume, aclose))
    results.reverse()
    d = np.array(results, dtype=stock_dt)
    if adjusted:
        scale = d['aclose'] / d['close']
        scale[np.isinf(scale)] = np.nan
        d['open'] *= scale
        d['high'] *= scale
        d['low'] *= scale
        d['close'] *= scale

    if not asobject:
        # 2-D sequence; formerly list of tuples, now ndarray
        ret = np.zeros((len(d), 6), dtype=np.float)
        ret[:, 0] = d['d']
        if ochl:
            ret[:, 1] = d['open']
            ret[:, 2] = d['close']
            ret[:, 3] = d['high']
            ret[:, 4] = d['low']
        else:
            ret[:, 1] = d['open']
            ret[:, 2] = d['high']
            ret[:, 3] = d['low']
            ret[:, 4] = d['close']
        ret[:, 5] = d['volume']
        if asobject is None:
            return ret
        return [tuple(row) for row in ret]

    return d.view(np.recarray)  # Close enough to former Bunch return


def fetch_historical_yahoo(ticker, date1, date2, cachename=None,
                           dividends=False):
    """
    Fetch historical data for ticker between date1 and date2.  date1 and
    date2 are date or datetime instances, or (year, month, day) sequences.

    Parameters
    ----------
    ticker : str
        ticker

    date1 : sequence of form (year, month, day), `datetime`, or `date`
        start date
    date2 : sequence of form (year, month, day), `datetime`, or `date`
        end date

    cachename : str
        cachename is the name of the local file cache.  If None, will
        default to the md5 hash or the url (which incorporates the ticker
        and date range)

    dividends : bool
        set dividends=True to return dividends instead of price data.  With
        this option set, parse functions will not work

    Returns
    -------
    file_handle : file handle
        a file handle is returned


    Examples
    --------
    >>> fh = fetch_historical_yahoo('^GSPC', (2000, 1, 1), (2001, 12, 31))

    """

    ticker = ticker.upper()

    if iterable(date1):
        d1 = (date1[1] - 1, date1[2], date1[0])
    else:
        d1 = (date1.month - 1, date1.day, date1.year)
    if iterable(date2):
        d2 = (date2[1] - 1, date2[2], date2[0])
    else:
        d2 = (date2.month - 1, date2.day, date2.year)

    if dividends:
        g = 'v'
        verbose.report('Retrieving dividends instead of prices')
    else:
        g = 'd'

    urlFmt = ('http://ichart.yahoo.com/table.csv?a=%d&b=%d&' +
              'c=%d&d=%d&e=%d&f=%d&s=%s&y=0&g=%s&ignore=.csv')

    url = urlFmt % (d1[0], d1[1], d1[2],
                    d2[0], d2[1], d2[2], ticker, g)

    # Cache the finance data if cachename is supplied, or there is a writable
    # cache directory.
    if cachename is None and cachedir is not None:
        cachename = os.path.join(cachedir, md5(url).hexdigest())
    if cachename is not None:
        if os.path.exists(cachename):
            fh = open(cachename)
            verbose.report('Using cachefile %s for '
                           '%s' % (cachename, ticker))
        else:
            mkdirs(os.path.abspath(os.path.dirname(cachename)))
            with contextlib.closing(urlopen(url)) as urlfh:
                with open(cachename, 'wb') as fh:
                    fh.write(urlfh.read())
            verbose.report('Saved %s data to cache file '
                           '%s' % (ticker, cachename))
            fh = open(cachename, 'r')

        return fh
    else:
        return urlopen(url)


def quotes_historical_yahoo(ticker, date1, date2, asobject=False,
                            adjusted=True, cachename=None):
    """ Get historical data for ticker between date1 and date2.


    This function has been deprecated in 1.4 in favor of
    `quotes_yahoo_historical_ochl`, which maintains the original argument
    order, or `quotes_yahoo_historical_ohlc`, which uses the
    open-high-low-close order.  This function will be removed in 1.5

    See :func:`parse_yahoo_historical` for explanation of output formats
    and the *asobject* and *adjusted* kwargs.

    Parameters
    ----------
    ticker : str
        stock ticker

    date1 : sequence of form (year, month, day), `datetime`, or `date`
        start date

    date2 : sequence of form (year, month, day), `datetime`, or `date`
        end date

    cachename : str or `None`
        is the name of the local file cache.  If None, will
        default to the md5 hash or the url (which incorporates the ticker
        and date range)

    Examples
    --------
    >>> sp = f.quotes_historical_yahoo('^GSPC', d1, d2,
                             asobject=True, adjusted=True)
    >>> returns = (sp.open[1:] - sp.open[:-1])/sp.open[1:]
    >>> [n,bins,patches] = hist(returns, 100)
    >>> mu = mean(returns)
    >>> sigma = std(returns)
    >>> x = normpdf(bins, mu, sigma)
    >>> plot(bins, x, color='red', lw=2)

    """
    warnings.warn(_warn_str.format(fun='quotes_historical_yahoo'),
                  mplDeprecation)

    return _quotes_historical_yahoo(ticker, date1, date2, asobject=asobject,
                             adjusted=adjusted, cachename=cachename,
                             ochl=True)


def quotes_historical_yahoo_ochl(ticker, date1, date2, asobject=False,
                            adjusted=True, cachename=None):
    """ Get historical data for ticker between date1 and date2.


    See :func:`parse_yahoo_historical` for explanation of output formats
    and the *asobject* and *adjusted* kwargs.

    Parameters
    ----------
    ticker : str
        stock ticker

    date1 : sequence of form (year, month, day), `datetime`, or `date`
        start date

    date2 : sequence of form (year, month, day), `datetime`, or `date`
        end date

    cachename : str or `None`
        is the name of the local file cache.  If None, will
        default to the md5 hash or the url (which incorporates the ticker
        and date range)

    Examples
    --------
    >>> sp = f.quotes_historical_yahoo_ochl('^GSPC', d1, d2,
                             asobject=True, adjusted=True)
    >>> returns = (sp.open[1:] - sp.open[:-1])/sp.open[1:]
    >>> [n,bins,patches] = hist(returns, 100)
    >>> mu = mean(returns)
    >>> sigma = std(returns)
    >>> x = normpdf(bins, mu, sigma)
    >>> plot(bins, x, color='red', lw=2)

    """

    return _quotes_historical_yahoo(ticker, date1, date2, asobject=asobject,
                             adjusted=adjusted, cachename=cachename,
                             ochl=True)


def quotes_historical_yahoo_ohlc(ticker, date1, date2, asobject=False,
                            adjusted=True, cachename=None):
    """ Get historical data for ticker between date1 and date2.


    See :func:`parse_yahoo_historical` for explanation of output formats
    and the *asobject* and *adjusted* kwargs.

    Parameters
    ----------
    ticker : str
        stock ticker

    date1 : sequence of form (year, month, day), `datetime`, or `date`
        start date

    date2 : sequence of form (year, month, day), `datetime`, or `date`
        end date

    cachename : str or `None`
        is the name of the local file cache.  If None, will
        default to the md5 hash or the url (which incorporates the ticker
        and date range)

    Examples
    --------
    >>> sp = f.quotes_historical_yahoo_ohlc('^GSPC', d1, d2,
                             asobject=True, adjusted=True)
    >>> returns = (sp.open[1:] - sp.open[:-1])/sp.open[1:]
    >>> [n,bins,patches] = hist(returns, 100)
    >>> mu = mean(returns)
    >>> sigma = std(returns)
    >>> x = normpdf(bins, mu, sigma)
    >>> plot(bins, x, color='red', lw=2)

    """

    return _quotes_historical_yahoo(ticker, date1, date2, asobject=asobject,
                             adjusted=adjusted, cachename=cachename,
                             ochl=False)


def _quotes_historical_yahoo(ticker, date1, date2, asobject=False,
                            adjusted=True, cachename=None,
                            ochl=True):
    """ Get historical data for ticker between date1 and date2.

    See :func:`parse_yahoo_historical` for explanation of output formats
    and the *asobject* and *adjusted* kwargs.

    Parameters
    ----------
    ticker : str
        stock ticker

    date1 : sequence of form (year, month, day), `datetime`, or `date`
        start date

    date2 : sequence of form (year, month, day), `datetime`, or `date`
        end date

    cachename : str or `None`
        is the name of the local file cache.  If None, will
        default to the md5 hash or the url (which incorporates the ticker
        and date range)

    ochl: bool
        temporary argument to select between ochl and ohlc ordering


    Examples
    --------
    >>> sp = f.quotes_historical_yahoo('^GSPC', d1, d2,
                             asobject=True, adjusted=True)
    >>> returns = (sp.open[1:] - sp.open[:-1])/sp.open[1:]
    >>> [n,bins,patches] = hist(returns, 100)
    >>> mu = mean(returns)
    >>> sigma = std(returns)
    >>> x = normpdf(bins, mu, sigma)
    >>> plot(bins, x, color='red', lw=2)

    """
    # Maybe enable a warning later as part of a slow transition
    # to using None instead of False.
    #if asobject is False:
    #    warnings.warn("Recommend changing to asobject=None")

    fh = fetch_historical_yahoo(ticker, date1, date2, cachename)

    try:
        ret = _parse_yahoo_historical(fh, asobject=asobject,
                                     adjusted=adjusted, ochl=ochl)
        if len(ret) == 0:
            return None
    except IOError as exc:
        warnings.warn('fh failure\n%s' % (exc.strerror[1]))
        return None

    return ret


def plot_day_summary(ax, quotes, ticksize=3,
                     colorup='k', colordown='r',
                     ):
    """Plots day summary

        Represent the time, open, close, high, low as a vertical line
        ranging from low to high.  The left tick is the open and the right
        tick is the close.


    This function has been deprecated in 1.4 in favor of
    `plot_day_summary_ochl`, which maintains the original argument
    order, or `plot_day_summary_ohlc`, which uses the
    open-high-low-close order.  This function will be removed in 1.5


    Parameters
    ----------
    ax : `Axes`
        an `Axes` instance to plot to
    quotes : sequence of (time, open, close, high, low, ...) sequences
        data to plot.  time must be in float date format - see date2num
    ticksize : int
        open/close tick marker in points
    colorup : color
        the color of the lines where close >= open
    colordown : color
        the color of the lines where close <  open

    Returns
    -------
    lines : list
        list of tuples of the lines added (one tuple per quote)
    """
    warnings.warn(_warn_str.format(fun='plot_day_summary'),
                  mplDeprecation)

    return _plot_day_summary(ax, quotes, ticksize=ticksize,
                     colorup=colorup, colordown=colordown,
                     ochl=True)


def plot_day_summary_oclh(ax, quotes, ticksize=3,
                     colorup='k', colordown='r',
                     ):
    """Plots day summary

        Represent the time, open, close, high, low as a vertical line
        ranging from low to high.  The left tick is the open and the right
        tick is the close.



    Parameters
    ----------
    ax : `Axes`
        an `Axes` instance to plot to
    quotes : sequence of (time, open, close, high, low, ...) sequences
        data to plot.  time must be in float date format - see date2num
    ticksize : int
        open/close tick marker in points
    colorup : color
        the color of the lines where close >= open
    colordown : color
        the color of the lines where close <  open

    Returns
    -------
    lines : list
        list of tuples of the lines added (one tuple per quote)
    """
    return _plot_day_summary(ax, quotes, ticksize=ticksize,
                     colorup=colorup, colordown=colordown,
                     ochl=True)


def plot_day_summary_ohlc(ax, quotes, ticksize=3,
                     colorup='k', colordown='r',
                      ):
    """Plots day summary

        Represent the time, open, high, low, close as a vertical line
        ranging from low to high.  The left tick is the open and the right
        tick is the close.



    Parameters
    ----------
    ax : `Axes`
        an `Axes` instance to plot to
    quotes : sequence of (time, open, high, low, close, ...) sequences
        data to plot.  time must be in float date format - see date2num
    ticksize : int
        open/close tick marker in points
    colorup : color
        the color of the lines where close >= open
    colordown : color
        the color of the lines where close <  open

    Returns
    -------
    lines : list
        list of tuples of the lines added (one tuple per quote)
    """
    return _plot_day_summary(ax, quotes, ticksize=ticksize,
                     colorup=colorup, colordown=colordown,
                     ochl=False)


def _plot_day_summary(ax, quotes, ticksize=3,
                     colorup='k', colordown='r',
                     ochl=True
                     ):
    """Plots day summary


        Represent the time, open, high, low, close as a vertical line
        ranging from low to high.  The left tick is the open and the right
        tick is the close.



    Parameters
    ----------
    ax : `Axes`
        an `Axes` instance to plot to
    quotes : sequence of quote sequences
        data to plot.  time must be in float date format - see date2num
        (time, open, high, low, close, ...) vs
        (time, open, close, high, low, ...)
        set by `ochl`
    ticksize : int
        open/close tick marker in points
    colorup : color
        the color of the lines where close >= open
    colordown : color
        the color of the lines where close <  open
    ochl: bool
        argument to select between ochl and ohlc ordering of quotes

    Returns
    -------
    lines : list
        list of tuples of the lines added (one tuple per quote)
    """
    # unfortunately this has a different return type than plot_day_summary2_*
    lines = []
    for q in quotes:
        if ochl:
            t, open, close, high, low = q[:5]
        else:
            t, open, high, low, close = q[:5]

        if close >= open:
            color = colorup
        else:
            color = colordown

        vline = Line2D(xdata=(t, t), ydata=(low, high),
                       color=color,
                       antialiased=False,   # no need to antialias vert lines
                       )

        oline = Line2D(xdata=(t, t), ydata=(open, open),
                       color=color,
                       antialiased=False,
                       marker=TICKLEFT,
                       markersize=ticksize,
                       )

        cline = Line2D(xdata=(t, t), ydata=(close, close),
                       color=color,
                       antialiased=False,
                       markersize=ticksize,
                       marker=TICKRIGHT)

        lines.extend((vline, oline, cline))
        ax.add_line(vline)
        ax.add_line(oline)
        ax.add_line(cline)

    ax.autoscale_view()

    return lines


def candlestick(ax, quotes, width=0.2, colorup='k', colordown='r',
                alpha=1.0):

    """
    Plot the time, open, close, high, low as a vertical line ranging
    from low to high.  Use a rectangular bar to represent the
    open-close span.  If close >= open, use colorup to color the bar,
    otherwise use colordown


    This function has been deprecated in 1.4 in favor of
    `candlestick_ochl`, which maintains the original argument
    order, or `candlestick_ohlc`, which uses the
    open-high-low-close order.  This function will be removed in 1.5


    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    quotes : sequence of (time, open, close, high, low, ...) sequences
        As long as the first 5 elements are these values,
        the record can be as long as you want (eg it may store volume).

        time must be in float days format - see date2num

    width : float
        fraction of a day for the rectangle width
    colorup : color
        the color of the rectangle where close >= open
    colordown : color
         the color of the rectangle where close <  open
    alpha : float
        the rectangle alpha level

    Returns
    -------
    ret : tuple
        returns (lines, patches) where lines is a list of lines
        added and patches is a list of the rectangle patches added

    """
    warnings.warn(_warn_str.format(fun='candlestick'),
                  mplDeprecation)

    return _candlestick(ax, quotes, width=width, colorup=colorup,
                        colordown=colordown,
                        alpha=alpha, ochl=True)


def candlestick_ochl(ax, quotes, width=0.2, colorup='k', colordown='r',
                alpha=1.0):

    """
    Plot the time, open, close, high, low as a vertical line ranging
    from low to high.  Use a rectangular bar to represent the
    open-close span.  If close >= open, use colorup to color the bar,
    otherwise use colordown

    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    quotes : sequence of (time, open, close, high, low, ...) sequences
        As long as the first 5 elements are these values,
        the record can be as long as you want (eg it may store volume).

        time must be in float days format - see date2num

    width : float
        fraction of a day for the rectangle width
    colorup : color
        the color of the rectangle where close >= open
    colordown : color
         the color of the rectangle where close <  open
    alpha : float
        the rectangle alpha level

    Returns
    -------
    ret : tuple
        returns (lines, patches) where lines is a list of lines
        added and patches is a list of the rectangle patches added

    """
    return _candlestick(ax, quotes, width=width, colorup=colorup,
                        colordown=colordown,
                        alpha=alpha, ochl=True)


def candlestick_ohlc(ax, quotes, width=0.2, colorup='k', colordown='r',
                alpha=1.0):

    """
    Plot the time, open, high, low, close as a vertical line ranging
    from low to high.  Use a rectangular bar to represent the
    open-close span.  If close >= open, use colorup to color the bar,
    otherwise use colordown

    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    quotes : sequence of (time, open, high, low, close, ...) sequences
        As long as the first 5 elements are these values,
        the record can be as long as you want (eg it may store volume).

        time must be in float days format - see date2num

    width : float
        fraction of a day for the rectangle width
    colorup : color
        the color of the rectangle where close >= open
    colordown : color
         the color of the rectangle where close <  open
    alpha : float
        the rectangle alpha level

    Returns
    -------
    ret : tuple
        returns (lines, patches) where lines is a list of lines
        added and patches is a list of the rectangle patches added

    """
    return _candlestick(ax, quotes, width=width, colorup=colorup,
                        colordown=colordown,
                        alpha=alpha, ochl=False)


def _candlestick(ax, quotes, width=0.2, colorup='k', colordown='r',
                alpha=1.0, ochl=True):

    """
    Plot the time, open, high, low, close as a vertical line ranging
    from low to high.  Use a rectangular bar to represent the
    open-close span.  If close >= open, use colorup to color the bar,
    otherwise use colordown

    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    quotes : sequence of quote sequences
        data to plot.  time must be in float date format - see date2num
        (time, open, high, low, close, ...) vs
        (time, open, close, high, low, ...)
        set by `ochl`
    width : float
        fraction of a day for the rectangle width
    colorup : color
        the color of the rectangle where close >= open
    colordown : color
         the color of the rectangle where close <  open
    alpha : float
        the rectangle alpha level
    ochl: bool
        argument to select between ochl and ohlc ordering of quotes

    Returns
    -------
    ret : tuple
        returns (lines, patches) where lines is a list of lines
        added and patches is a list of the rectangle patches added

    """

    OFFSET = width / 2.0

    lines = []
    patches = []
    for q in quotes:
        if ochl:
            t, open, close, high, low = q[:5]
        else:
            t, open, high, low, close = q[:5]

        if close >= open:
            color = colorup
            lower = open
            height = close - open
        else:
            color = colordown
            lower = close
            height = open - close

        vline = Line2D(
            xdata=(t, t), ydata=(low, high),
            color='k',
            linewidth=0.5,
            antialiased=True,
        )

        rect = Rectangle(
            xy=(t - OFFSET, lower),
            width = width,
            height = height,
            facecolor = color,
            edgecolor = color,
        )
        rect.set_alpha(alpha)

        lines.append(vline)
        patches.append(rect)
        ax.add_line(vline)
        ax.add_patch(rect)
    ax.autoscale_view()

    return lines, patches


def plot_day_summary2(ax, opens, closes, highs, lows, ticksize=4,
                      colorup='k', colordown='r',
                      ):
    """Represent the time, open, close, high, low,  as a vertical line
    ranging from low to high.  The left tick is the open and the right
    tick is the close.


    This function has been deprecated in 1.4 in favor of
    `plot_day_summary2_ochl`, which maintains the original argument
    order, or `plot_day_summary2_ohlc`, which uses the
    open-high-low-close order.  This function will be removed in 1.5


    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    opens : sequence
        sequence of opening values
    closes : sequence
        sequence of closing values
    highs : sequence
        sequence of high values
    lows : sequence
        sequence of low values
    ticksize : int
        size of open and close ticks in points
    colorup : color
        the color of the lines where close >= open
    colordown : color
         the color of the lines where close <  open

    Returns
    -------
    ret : list
        a list of lines added to the axes
    """

    warnings.warn(_warn_str.format(fun='plot_day_summary2'), mplDeprecation)
    return plot_day_summary2_ohlc(ax, opens, highs, lows, closes, ticksize,
                                 colorup, colordown)


def plot_day_summary2_ochl(ax, opens, closes, highs, lows, ticksize=4,
                          colorup='k', colordown='r',
                          ):

    """Represent the time, open, close, high, low,  as a vertical line
    ranging from low to high.  The left tick is the open and the right
    tick is the close.

    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    opens : sequence
        sequence of opening values
    closes : sequence
        sequence of closing values
    highs : sequence
        sequence of high values
    lows : sequence
        sequence of low values
    ticksize : int
        size of open and close ticks in points
    colorup : color
        the color of the lines where close >= open
    colordown : color
         the color of the lines where close <  open

    Returns
    -------
    ret : list
        a list of lines added to the axes
    """

    return plot_day_summary2_ohlc(ax, opens, highs, lows, closes, ticksize,
                                 colorup, colordown)


def plot_day_summary2_ohlc(ax, opens, highs, lows, closes, ticksize=4,
                          colorup='k', colordown='r',
                          ):

    """Represent the time, open, high, low, close as a vertical line
    ranging from low to high.  The left tick is the open and the right
    tick is the close.

    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    opens : sequence
        sequence of opening values
    highs : sequence
        sequence of high values
    lows : sequence
        sequence of low values
    closes : sequence
        sequence of closing values
    ticksize : int
        size of open and close ticks in points
    colorup : color
        the color of the lines where close >= open
    colordown : color
         the color of the lines where close <  open

    Returns
    -------
    ret : list
        a list of lines added to the axes
    """
    # note this code assumes if any value open, high, low, close is
    # missing they all are missing

    rangeSegments = [((i, low), (i, high)) for i, low, high in
                     zip(xrange(len(lows)), lows, highs) if low != -1]

    # the ticks will be from ticksize to 0 in points at the origin and
    # we'll translate these to the i, close location
    openSegments = [((-ticksize, 0), (0, 0))]

    # the ticks will be from 0 to ticksize in points at the origin and
    # we'll translate these to the i, close location
    closeSegments = [((0, 0), (ticksize, 0))]

    offsetsOpen = [(i, open) for i, open in
                   zip(xrange(len(opens)), opens) if open != -1]

    offsetsClose = [(i, close) for i, close in
                    zip(xrange(len(closes)), closes) if close != -1]

    scale = ax.figure.dpi * (1.0 / 72.0)

    tickTransform = Affine2D().scale(scale, 0.0)

    r, g, b = colorConverter.to_rgb(colorup)
    colorup = r, g, b, 1
    r, g, b = colorConverter.to_rgb(colordown)
    colordown = r, g, b, 1
    colord = {True: colorup,
              False: colordown,
              }
    colors = [colord[open < close] for open, close in
              zip(opens, closes) if open != -1 and close != -1]

    assert(len(rangeSegments) == len(offsetsOpen))
    assert(len(offsetsOpen) == len(offsetsClose))
    assert(len(offsetsClose) == len(colors))

    useAA = 0,   # use tuple here
    lw = 1,      # and here
    rangeCollection = LineCollection(rangeSegments,
                                     colors=colors,
                                     linewidths=lw,
                                     antialiaseds=useAA,
                                     )

    openCollection = LineCollection(openSegments,
                                    colors=colors,
                                    antialiaseds=useAA,
                                    linewidths=lw,
                                    offsets=offsetsOpen,
                                    transOffset=ax.transData,
                                    )
    openCollection.set_transform(tickTransform)

    closeCollection = LineCollection(closeSegments,
                                     colors=colors,
                                     antialiaseds=useAA,
                                     linewidths=lw,
                                     offsets=offsetsClose,
                                     transOffset=ax.transData,
                                     )
    closeCollection.set_transform(tickTransform)

    minpy, maxx = (0, len(rangeSegments))
    miny = min([low for low in lows if low != -1])
    maxy = max([high for high in highs if high != -1])
    corners = (minpy, miny), (maxx, maxy)
    ax.update_datalim(corners)
    ax.autoscale_view()

    # add these last
    ax.add_collection(rangeCollection)
    ax.add_collection(openCollection)
    ax.add_collection(closeCollection)
    return rangeCollection, openCollection, closeCollection


def candlestick2_ochl(ax, opens, closes, highs, lows,  width=4,
                 colorup='k', colordown='r',
                 alpha=0.75,
                 ):
    """Represent the open, close as a bar line and high low range as a
    vertical line.

    Preserves the original argument order.


    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    opens : sequence
        sequence of opening values
    closes : sequence
        sequence of closing values
    highs : sequence
        sequence of high values
    lows : sequence
        sequence of low values
    ticksize : int
        size of open and close ticks in points
    colorup : color
        the color of the lines where close >= open
    colordown : color
        the color of the lines where close <  open
    alpha : float
        bar transparency

    Returns
    -------
    ret : tuple
        (lineCollection, barCollection)
    """

    candlestick2_ohlc(ax, opens, highs, closes, lows, width=width,
                     colorup=colorup, colordown=colordown,
                     alpha=alpha)


def candlestick2(ax, opens, closes, highs, lows,  width=4,
                 colorup='k', colordown='r',
                 alpha=0.75,
                 ):
    """Represent the open, close as a bar line and high low range as a
    vertical line.

    This function has been deprecated in 1.4 in favor of
    `candlestick2_ochl`, which maintains the original argument order,
    or `candlestick2_ohlc`, which uses the open-high-low-close order.
    This function will be removed in 1.5


    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    opens : sequence
        sequence of opening values
    closes : sequence
        sequence of closing values
    highs : sequence
        sequence of high values
    lows : sequence
        sequence of low values
    ticksize : int
        size of open and close ticks in points
    colorup : color
        the color of the lines where close >= open
    colordown : color
        the color of the lines where close <  open
    alpha : float
        bar transparency

    Returns
    -------
    ret : tuple
        (lineCollection, barCollection)
    """
    warnings.warn(_warn_str.format(fun='candlestick2'),
                  mplDeprecation)

    candlestick2_ohlc(ax, opens, highs, lows, closes, width=width,
                     colorup=colorup, colordown=colordown,
                     alpha=alpha)


def candlestick2_ohlc(ax, opens, highs, lows, closes, width=4,
                 colorup='k', colordown='r',
                 alpha=0.75,
                 ):
    """Represent the open, close as a bar line and high low range as a
    vertical line.


    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    opens : sequence
        sequence of opening values
    highs : sequence
        sequence of high values
    lows : sequence
        sequence of low values
    closes : sequence
        sequence of closing values
    ticksize : int
        size of open and close ticks in points
    colorup : color
        the color of the lines where close >= open
    colordown : color
        the color of the lines where close <  open
    alpha : float
        bar transparency

    Returns
    -------
    ret : tuple
        (lineCollection, barCollection)
    """

    # note this code assumes if any value open, low, high, close is
    # missing they all are missing

    delta = width / 2.
    barVerts = [((i - delta, open),
                 (i - delta, close),
                 (i + delta, close),
                 (i + delta, open))
                for i, open, close in zip(xrange(len(opens)), opens, closes)
                if open != -1 and close != -1]

    rangeSegments = [((i, low), (i, high))
                     for i, low, high in zip(xrange(len(lows)), lows, highs)
                     if low != -1]

    r, g, b = colorConverter.to_rgb(colorup)
    colorup = r, g, b, alpha
    r, g, b = colorConverter.to_rgb(colordown)
    colordown = r, g, b, alpha
    colord = {True: colorup,
              False: colordown,
              }
    colors = [colord[open < close]
              for open, close in zip(opens, closes)
              if open != -1 and close != -1]

    assert(len(barVerts) == len(rangeSegments))

    useAA = 0,  # use tuple here
    lw = 0.5,   # and here
    rangeCollection = LineCollection(rangeSegments,
                                     colors=((0, 0, 0, 1), ),
                                     linewidths=lw,
                                     antialiaseds = useAA,
                                     )

    barCollection = PolyCollection(barVerts,
                                   facecolors=colors,
                                   edgecolors=((0, 0, 0, 1), ),
                                   antialiaseds=useAA,
                                   linewidths=lw,
                                   )

    minx, maxx = 0, len(rangeSegments)
    miny = min([low for low in lows if low != -1])
    maxy = max([high for high in highs if high != -1])

    corners = (minx, miny), (maxx, maxy)
    ax.update_datalim(corners)
    ax.autoscale_view()

    # add these last
    ax.add_collection(barCollection)
    ax.add_collection(rangeCollection)
    return rangeCollection, barCollection


def volume_overlay(ax, opens, closes, volumes,
                   colorup='k', colordown='r',
                   width=4, alpha=1.0):
    """Add a volume overlay to the current axes.  The opens and closes
    are used to determine the color of the bar.  -1 is missing.  If a
    value is missing on one it must be missing on all

    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    opens : sequence
        a sequence of opens
    closes : sequence
        a sequence of closes
    volumes : sequence
        a sequence of volumes
    width : int
        the bar width in points
    colorup : color
        the color of the lines where close >= open
    colordown : color
        the color of the lines where close <  open
    alpha : float
        bar transparency

    Returns
    -------
    ret : `barCollection`
        The `barrCollection` added to the axes

    """

    r, g, b = colorConverter.to_rgb(colorup)
    colorup = r, g, b, alpha
    r, g, b = colorConverter.to_rgb(colordown)
    colordown = r, g, b, alpha
    colord = {True: colorup,
              False: colordown,
              }
    colors = [colord[open < close]
              for open, close in zip(opens, closes)
              if open != -1 and close != -1]

    delta = width / 2.
    bars = [((i - delta, 0), (i - delta, v), (i + delta, v), (i + delta, 0))
            for i, v in enumerate(volumes)
            if v != -1]

    barCollection = PolyCollection(bars,
                                   facecolors=colors,
                                   edgecolors=((0, 0, 0, 1), ),
                                   antialiaseds=(0,),
                                   linewidths=(0.5,),
                                   )

    ax.add_collection(barCollection)
    corners = (0, 0), (len(bars), max(volumes))
    ax.update_datalim(corners)
    ax.autoscale_view()

    # add these last
    return barCollection


def volume_overlay2(ax, closes, volumes,
                    colorup='k', colordown='r',
                    width=4, alpha=1.0):
    """
    Add a volume overlay to the current axes.  The closes are used to
    determine the color of the bar.  -1 is missing.  If a value is
    missing on one it must be missing on all

    nb: first point is not displayed - it is used only for choosing the
    right color


    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    closes : sequence
        a sequence of closes
    volumes : sequence
        a sequence of volumes
    width : int
        the bar width in points
    colorup : color
        the color of the lines where close >= open
    colordown : color
        the color of the lines where close <  open
    alpha : float
        bar transparency

    Returns
    -------
    ret : `barCollection`
        The `barrCollection` added to the axes

    """

    return volume_overlay(ax, closes[:-1], closes[1:], volumes[1:],
                          colorup, colordown, width, alpha)


def volume_overlay3(ax, quotes,
                    colorup='k', colordown='r',
                    width=4, alpha=1.0):
    """Add a volume overlay to the current axes.  quotes is a list of (d,
    open, high, low, close, volume) and close-open is used to
    determine the color of the bar

    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    quotes : sequence of (time, open, high, low, close, ...) sequences
        data to plot.  time must be in float date format - see date2num
    width : int
        the bar width in points
    colorup : color
        the color of the lines where close1 >= close0
    colordown : color
        the color of the lines where close1 <  close0
    alpha : float
         bar transparency

    Returns
    -------
    ret : `barCollection`
        The `barrCollection` added to the axes


    """

    r, g, b = colorConverter.to_rgb(colorup)
    colorup = r, g, b, alpha
    r, g, b = colorConverter.to_rgb(colordown)
    colordown = r, g, b, alpha
    colord = {True: colorup,
              False: colordown,
              }

    dates, opens, highs, lows, closes, volumes = zip(*quotes)
    colors = [colord[close1 >= close0]
              for close0, close1 in zip(closes[:-1], closes[1:])
              if close0 != -1 and close1 != -1]
    colors.insert(0, colord[closes[0] >= opens[0]])

    right = width / 2.0
    left = -width / 2.0

    bars = [((left, 0), (left, volume), (right, volume), (right, 0))
            for d, open, high, low, close, volume in quotes]

    sx = ax.figure.dpi * (1.0 / 72.0)  # scale for points
    sy = ax.bbox.height / ax.viewLim.height

    barTransform = Affine2D().scale(sx, sy)

    dates = [d for d, open, high, low, close, volume in quotes]
    offsetsBars = [(d, 0) for d in dates]

    useAA = 0,  # use tuple here
    lw = 0.5,   # and here
    barCollection = PolyCollection(bars,
                                   facecolors=colors,
                                   edgecolors=((0, 0, 0, 1),),
                                   antialiaseds=useAA,
                                   linewidths=lw,
                                   offsets=offsetsBars,
                                   transOffset=ax.transData,
                                   )
    barCollection.set_transform(barTransform)

    minpy, maxx = (min(dates), max(dates))
    miny = 0
    maxy = max([volume for d, open, high, low, close, volume in quotes])
    corners = (minpy, miny), (maxx, maxy)
    ax.update_datalim(corners)
    #print 'datalim', ax.dataLim.bounds
    #print 'viewlim', ax.viewLim.bounds

    ax.add_collection(barCollection)
    ax.autoscale_view()

    return barCollection


def index_bar(ax, vals,
              facecolor='b', edgecolor='l',
              width=4, alpha=1.0, ):
    """Add a bar collection graph with height vals (-1 is missing).

    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    vals : sequence
        a sequence of values
    facecolor : color
        the color of the bar face
    edgecolor : color
        the color of the bar edges
    width : int
        the bar width in points
    alpha : float
       bar transparency

    Returns
    -------
    ret : `barCollection`
        The `barrCollection` added to the axes

    """

    facecolors = (colorConverter.to_rgba(facecolor, alpha),)
    edgecolors = (colorConverter.to_rgba(edgecolor, alpha),)

    right = width / 2.0
    left = -width / 2.0

    bars = [((left, 0), (left, v), (right, v), (right, 0))
            for v in vals if v != -1]

    sx = ax.figure.dpi * (1.0 / 72.0)  # scale for points
    sy = ax.bbox.height / ax.viewLim.height

    barTransform = Affine2D().scale(sx, sy)

    offsetsBars = [(i, 0) for i, v in enumerate(vals) if v != -1]

    barCollection = PolyCollection(bars,
                                   facecolors=facecolors,
                                   edgecolors=edgecolors,
                                   antialiaseds=(0,),
                                   linewidths=(0.5,),
                                   offsets=offsetsBars,
                                   transOffset=ax.transData,
                                   )
    barCollection.set_transform(barTransform)

    minpy, maxx = (0, len(offsetsBars))
    miny = 0
    maxy = max([v for v in vals if v != -1])
    corners = (minpy, miny), (maxx, maxy)
    ax.update_datalim(corners)
    ax.autoscale_view()

    # add these last
    ax.add_collection(barCollection)
    return barCollection