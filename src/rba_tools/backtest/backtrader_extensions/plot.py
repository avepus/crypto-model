from collections import defaultdict
from dataclasses import dataclass
import backtrader as bt
from datetime import datetime
import plotly.graph_objects as go
from backtrader.utils import num2date
import pandas as pd
import numpy as np

from rba_tools.retriever.get_crypto_data import DataPuller
from rba_tools.backtest.backtrader_extensions.strategies import MaCrossStrategy

GLOBAL_TOP = 'global_top'
UPPER = 'upper'
LOWER = 'lower'
OVERLAY = 'overlay'


def main():
    cerebro = bt.Cerebro(runonce=False)

    cerebro.addstrategy(MaCrossStrategy)
    puller = DataPuller.kraken_puller()

    #symbol and date range
    symbol = 'ETH/USD'
    from_date = '1/1/20'
    to_date = '6/30/20'

    dataframe = puller.fetch_df(symbol, 'h', from_date, to_date)

    # Pass it to the backtrader datafeed and add it to the cerebro
    data = bt.feeds.PandasData(dataname=dataframe,
                                nocase=True,
                                )
    #cerebro.adddata(data)
    cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes, compression=240)

    cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes, compression=1440)

    # Run over everything
    back = cerebro.run()
    myp = cerebro.plot(numfigs=1, style='bar')

    #my_plot(back[0])



def get_datetime(strategy):
    datetime_series = pd.Series(strategy.datetime.plot())
    datetime_array = datetime_series.map(num2date)
    return pd.to_datetime(datetime_array)


def rbs_sort_indicators(strategy: bt.Strategy):
    # These lists/dictionaries hold the subplots that go above each data
    plot_dictionary = {
        GLOBAL_TOP : list(),
        UPPER : defaultdict(list),
        LOWER : defaultdict(list),
        OVERLAY : defaultdict(list)
    }

    # Sort observers in the different lists/dictionaries
    for observer in strategy.getobservers():
        if not observer.plotinfo.plot or observer.plotinfo.plotskip:
            continue

        if observer.plotinfo.subplot:
            plot_dictionary[GLOBAL_TOP].append(observer)
        else:
            key = getattr(observer._clock, 'owner', observer._clock)
            plot_dictionary[OVERLAY][key].append(observer)

    # Sort indicators in the different lists/dictionaries
    for indicator in strategy.getindicators():
        if not hasattr(indicator, 'plotinfo'):
            # no plotting support - so far LineSingle derived classes
            continue

        if not indicator.plotinfo.plot or indicator.plotinfo.plotskip:
            continue

        indicator._plotinit()  # will be plotted ... call its init function

        # support LineSeriesStub which has "owner" to point to the data
        key = getattr(indicator._clock, 'owner', indicator._clock)
        if key is strategy:  # a LinesCoupler
            key = strategy.data

        if getattr(indicator.plotinfo, 'plotforce', False):
            if key not in strategy.datas:
                datas = strategy.datas
                while True:
                    if key not in strategy.datas:
                        key = key._clock
                    else:
                        break

        xpmaster = indicator.plotinfo.plotmaster
        if xpmaster is indicator:
            xpmaster = None
        if xpmaster is not None:
            key = xpmaster

        if indicator.plotinfo.subplot and xpmaster is None:
            if indicator.plotinfo.plotabove:
                plot_dictionary[UPPER][key].append(indicator)
            else:
                plot_dictionary[LOWER][key].append(indicator)
        else:
            plot_dictionary[OVERLAY][key].append(indicator)

    return plot_dictionary


def get_ohlcv_data_from_data(data):
    #get ohlcv dataframe from a backtrader feed
    start = 0
    end = len(data)
    datetime_float_ary = data.datetime.plot()
    datetime_list = [num2date(float_date) for float_date in datetime_float_ary]
    index = np.array(datetime_list)
    return pd.DataFrame(data={
        'Open' : data.open.plotrange(start,end),
        'High' : data.high.plotrange(start,end),
        'Low' : data.low.plotrange(start,end),
        'Close' : data.close.plotrange(start,end),
        'Volume' : data.volume.plotrange(start,end)
        },
        index=index)

#my attempt
def my_plot(strategy, plotter=None, start=None, end=None, **kwargs):
    #if self._exactbars > 0:
    #    return

    df_list = list()

    sorted_indicators = rbs_sort_indicators(strategy)

    for index in range(len(strategy.datas)):
        data = strategy.datas[index]
        df = get_ohlcv_data_from_data(data)

        if index == 0:
            #add global top indicators only to the first data
            for indicator in sorted_indicators[GLOBAL_TOP]:
                add_all_sorted_indicators_to_df(df, indicator, sorted_indicators)
        
        for indicator in sorted_indicators[UPPER][data]:
            add_all_sorted_indicators_to_df(df, indicator, sorted_indicators)

        for indicator in sorted_indicators[OVERLAY][data]:
            add_all_sorted_indicators_to_df(df, indicator, sorted_indicators)

        for indicator in sorted_indicators[LOWER][data]:
            add_all_sorted_indicators_to_df(df, indicator, sorted_indicators)

        df_list.append(df)

    return df_list
        
    #do the plotting


# @dataclass
# class Data

def add_all_sorted_indicators_to_df(df: pd.DataFrame, indicator: bt.indicator, sorted_indicators: True):
    """adds mapped top and bottom indicators and the passed in indicator to dataframe"""
    for inner_indicator in sorted_indicators[UPPER][indicator]:
        add_all_sorted_indicators_to_df(df, inner_indicator, sorted_indicators)
    
    add_indicator_to_df(df, indicator, inplace=True)

    for inner_indicator in sorted_indicators[LOWER][indicator]:
        add_all_sorted_indicators_to_df(df, inner_indicator, sorted_indicators)

def add_indicator_to_df(df: pd.DataFrame, indicator: bt.indicator, inplace=False):
    """adds an indicator and all of it's lines to a dataframe"""
    ret_df = df
    if not inplace:
        ret_df = df.copy()

    for line_index in range(indicator.size()):
        line = indicator.lines[line_index]
        name = get_indicator_line_name(indicator, line_index)
        indicator_vals = line.plotrange(0, len(line))

        ret_df[name] = indicator_vals
    return ret_df

def get_indicator_params_string(indicator: bt.indicator):
    """gets formatted paramaters from an indicator. They will be formatted as like so
    "param1name=value param2name=value ..."
    """
    params_str = ''
    param_dictionary = vars(indicator.p)
    if not param_dictionary:
        return params_str
    
    for key, value in param_dictionary.items():
        params_str += f' {key}={value}'
    
    return params_str.strip()


def get_indicator_line_name(indicator: bt.indicator, index=0):
    alias = indicator.lines._getlinealias(index)
    return alias + ' (' + get_indicator_params_string(indicator) + ')'


def testplotind(indicator: bt.indicator, x_axis, same_graph_inds=None, upinds=None, downinds=None):
    """returns a list of ploytly graph objects"""

    plotlist = []

    # check subind
    same_graph_inds = same_graph_inds or []
    upinds = upinds or []
    downinds = downinds or []

    for indicator in upinds:
        plotlist.append(testplotind(indicator, x_axis))


    for line_index in range(indicator.size()):
        line = indicator.lines[line_index]

        line_plot_info = get_line_plot_info(indicator, line_index)

        if line_plot_info._get('_plotskip', False):
            continue
        
        #gets the kwargs from the indicator that tell how it's plotted
        line_plot_kwargs = line_plot_info._getkwargs(skip_=True)

        # plot data
        indicator_vals = line.plotrange(0, len(line))

        plotlist.append(go.Scatter(x=x_axis,y=np.array(indicator_vals)))
    
    for indicator in downinds:
        plotlist.append(testplotind(indicator, x_axis))

    return plotlist


def get_line_plot_info(indicator:bt.indicator, line_index: int):
    """get the lineplotinfo from an indicator"""
    line_plot_info = getattr(indicator.plotlines, '_%d' % line_index, None)
    if line_plot_info:
        return line_plot_info
    
    linealias = indicator.lines._getlinealias(line_index)
    line_plot_info = getattr(indicator.plotlines, linealias, None)
    if line_plot_info:
        return line_plot_info

    #bt.AutoInfoClass() is what backtrader gets as the plot_info if we can't get it from the line
    return bt.AutoInfoClass()


def plot(self, strategy, figid=0, numfigs=1, iplot=True, **kwargs):
        # pfillers={}):
        if not strategy.datas:
            return

        if not len(strategy):
            return

        self.sortdataindicators(strategy)
        self.calcrows(strategy)

        st_dtime = strategy.lines.datetime.plot()
        start = 0
        end = len(st_dtime)

        # slen = len(st_dtime[start:end])
        # d, m = divmod(slen, numfigs)
        # pranges = list()
        # for i in range(numfigs):
        #     a = d * i + start
        #     if i == (numfigs - 1):
        #         d += m  # add remainder to last stint
        #     b = a + d

        #     pranges.append([a, b, d])

        figs = []

        # prepare a figure
        fig = self.pinf.newfig(figid, numfig, self.mpyplot)
        figs.append(fig)

        self.pinf.pstart, self.pinf.pend, self.pinf.psize = pranges[numfig]
        self.pinf.xstart = self.pinf.pstart
        self.pinf.xend = self.pinf.pend

        self.pinf.clock = strategy
        self.pinf.xreal = self.pinf.clock.datetime.plot(
            self.pinf.pstart, self.pinf.psize)
        self.pinf.xlen = len(self.pinf.xreal)
        self.pinf.x = list(range(self.pinf.xlen))
        # self.pinf.pfillers = {None: []}
        # for key, val in pfillers.items():
        #     pfstart = bisect.bisect_left(val, self.pinf.pstart)
        #     pfend = bisect.bisect_right(val, self.pinf.pend)
        #     self.pinf.pfillers[key] = val[pfstart:pfend]

        # Do the plotting
        # Things that go always at the top (observers)
        for ptop in self.dplotstop:
            self.plotind(None, ptop, subinds=self.dplotsover[ptop])

        # Create the rest on a per data basis
        for data in strategy.datas:
            if not data.plotinfo.plot:
                continue

            self.pinf.xdata = self.pinf.x
            xd = data.datetime.plotrange(self.pinf.xstart, self.pinf.xend)
            if len(xd) < self.pinf.xlen:
                self.pinf.xdata = xdata = []
                xreal = self.pinf.xreal
                dts = data.datetime.plot()
                xtemp = list()
                for dt in (x for x in dts if dt0 <= x <= dt1):
                    dtidx = bisect.bisect_left(xreal, dt)
                    xdata.append(dtidx)
                    xtemp.append(dt)

                self.pinf.xstart = bisect.bisect_left(dts, xtemp[0])
                self.pinf.xend = bisect.bisect_right(dts, xtemp[-1])

            for ind in self.dplotsup[data]:
                self.plotind(
                    data,
                    ind,
                    subinds=self.dplotsover[ind],
                    upinds=self.dplotsup[ind],
                    downinds=self.dplotsdown[ind])

            self.plotdata(data, self.dplotsover[data])

            for ind in self.dplotsdown[data]:
                self.plotind(
                    data,
                    ind,
                    subinds=self.dplotsover[ind],
                    upinds=self.dplotsup[ind],
                    downinds=self.dplotsdown[ind])


        return figs


def plotind(self, iref, ind,
                subinds=None, upinds=None, downinds=None,
                masterax=None):

        sch = self.p.scheme

        # check subind
        subinds = subinds or []
        upinds = upinds or []
        downinds = downinds or []

        # plot subindicators on self with independent axis above
        for upind in upinds:
            self.plotind(iref, upind)

        # Get an axis for this plot
        ax = masterax or self.newaxis(ind, rowspan=self.pinf.sch.rowsminor)

        indlabel = ind.plotlabel()

        for lineidx in range(ind.size()):
            line = ind.lines[lineidx]
            linealias = ind.lines._getlinealias(lineidx)

            lineplotinfo = getattr(ind.plotlines, '_%d' % lineidx, None)
            if not lineplotinfo:
                lineplotinfo = getattr(ind.plotlines, linealias, None)

            if not lineplotinfo:
                lineplotinfo = bt.AutoInfoClass()

            if lineplotinfo._get('_plotskip', False):
                continue


            # plot data
            lplot = line.plotrange(self.pinf.xstart, self.pinf.xend)

            # Global and generic for indicator
            if self.pinf.sch.linevalues and ind.plotinfo.plotlinevalues:
                plotlinevalue = lineplotinfo._get('_plotvalue', True)
                if plotlinevalue and not math.isnan(lplot[-1]):
                    label += ' %.2f' % lplot[-1]

            plotkwargs = dict()
            linekwargs = lineplotinfo._getkwargs(skip_=True)

            if linekwargs.get('color', None) is None:
                if not lineplotinfo._get('_samecolor', False):
                    self.pinf.nextcolor(ax)
                plotkwargs['color'] = self.pinf.color(ax)

            plotkwargs.update(dict(aa=True, label=label))
            plotkwargs.update(**linekwargs)

            if ax in self.pinf.zorder:
                plotkwargs['zorder'] = self.pinf.zordernext(ax)

            pltmethod = getattr(ax, lineplotinfo._get('_method', 'plot'))

            xdata, lplotarray = self.pinf.xdata, lplot
            if lineplotinfo._get('_skipnan', False):
                # Get the full array and a mask to skipnan
                lplotarray = np.array(lplot)
                lplotmask = np.isfinite(lplotarray)

                # Get both the axis and the data masked
                lplotarray = lplotarray[lplotmask]
                xdata = np.array(xdata)[lplotmask]

            plottedline = pltmethod(xdata, lplotarray, **plotkwargs)
            try:
                plottedline = plottedline[0]
            except:
                # Possibly a container of artists (when plotting bars)
                pass

            self.pinf.zorder[ax] = plottedline.get_zorder()

            vtags = lineplotinfo._get('plotvaluetags', True)
            if self.pinf.sch.valuetags and vtags:
                linetag = lineplotinfo._get('_plotvaluetag', True)
                if linetag and not math.isnan(lplot[-1]):
                    # line has valid values, plot a tag for the last value
                    self.drawtag(ax, len(self.pinf.xreal), lplot[-1],
                                 facecolor='white',
                                 edgecolor=self.pinf.color(ax))

            farts = (('_gt', operator.gt), ('_lt', operator.lt), ('', None),)
            for fcmp, fop in farts:
                fattr = '_fill' + fcmp
                fref, fcol = lineplotinfo._get(fattr, (None, None))
                if fref is not None:
                    y1 = np.array(lplot)
                    if isinstance(fref, integer_types):
                        y2 = np.full_like(y1, fref)
                    else:  # string, naming a line, nothing else is supported
                        l2 = getattr(ind, fref)
                        prl2 = l2.plotrange(self.pinf.xstart, self.pinf.xend)
                        y2 = np.array(prl2)
                    kwargs = dict()
                    if fop is not None:
                        kwargs['where'] = fop(y1, y2)

                    falpha = self.pinf.sch.fillalpha
                    if isinstance(fcol, (list, tuple)):
                        fcol, falpha = fcol

                    ax.fill_between(self.pinf.xdata, y1, y2,
                                    facecolor=fcol,
                                    alpha=falpha,
                                    interpolate=True,
                                    **kwargs)

        # plot subindicators that were created on self
        for subind in subinds:
            self.plotind(iref, subind, subinds=self.dplotsover[subind],
                         masterax=ax)

        if not masterax:
            # adjust margin if requested ... general of particular
            ymargin = ind.plotinfo._get('plotymargin', 0.0)
            ymargin = max(ymargin, self.pinf.sch.yadjust)
            if ymargin:
                ax.margins(y=ymargin)

            # Set specific or generic ticks
            yticks = ind.plotinfo._get('plotyticks', [])
            if not yticks:
                yticks = ind.plotinfo._get('plotyhlines', [])

            if yticks:
                ax.set_yticks(yticks)
            else:
                locator = mticker.MaxNLocator(nbins=4, prune='both')
                ax.yaxis.set_major_locator(locator)

            # Set specific hlines if asked to
            hlines = ind.plotinfo._get('plothlines', [])
            if not hlines:
                hlines = ind.plotinfo._get('plotyhlines', [])
            for hline in hlines:
                ax.axhline(hline, color=self.pinf.sch.hlinescolor,
                           ls=self.pinf.sch.hlinesstyle,
                           lw=self.pinf.sch.hlineswidth)

            if self.pinf.sch.legendind and \
               ind.plotinfo._get('plotlegend', True):

                handles, labels = ax.get_legend_handles_labels()
                # Ensure that we have something to show
                if labels:
                    # location can come from the user
                    loc = ind.plotinfo.legendloc or self.pinf.sch.legendindloc

                    # Legend done here to ensure it includes all plots
                    legend = ax.legend(loc=loc,
                                       numpoints=1, frameon=False,
                                       shadow=False, fancybox=False,
                                       prop=self.pinf.prop)

                    # legend.set_title(indlabel, prop=self.pinf.prop)
                    # hack: if title is set. legend has a Vbox for the labels
                    # which has a default "center" set
                    legend._legend_box.align = 'left'

        # plot subindicators on self with independent axis below
        for downind in downinds:
            self.plotind(iref, downind)












#code from backtrader.cerebro.plot is below
def plot(self, plotter=None, numfigs=1, iplot=True, start=None, end=None,
             width=16, height=9, dpi=300, tight=True, use=None,
             **kwargs):
        '''
        Plots the strategies inside cerebro

        If ``plotter`` is None a default ``Plot`` instance is created and
        ``kwargs`` are passed to it during instantiation.

        ``numfigs`` split the plot in the indicated number of charts reducing
        chart density if wished

        ``iplot``: if ``True`` and running in a ``notebook`` the charts will be
        displayed inline

        ``use``: set it to the name of the desired matplotlib backend. It will
        take precedence over ``iplot``

        ``start``: An index to the datetime line array of the strategy or a
        ``datetime.date``, ``datetime.datetime`` instance indicating the start
        of the plot

        ``end``: An index to the datetime line array of the strategy or a
        ``datetime.date``, ``datetime.datetime`` instance indicating the end
        of the plot

        ``width``: in inches of the saved figure

        ``height``: in inches of the saved figure

        ``dpi``: quality in dots per inches of the saved figure

        ``tight``: only save actual content and not the frame of the figure
        '''
        if self._exactbars > 0:
            return

        if not plotter:
            from backtrader import plot
            if self.p.oldsync:
                plotter = plot.Plot_OldSync(**kwargs)
            else:
                plotter = plot.Plot(**kwargs)

        # pfillers = {self.datas[i]: self._plotfillers[i]
        # for i, x in enumerate(self._plotfillers)}

        # pfillers2 = {self.datas[i]: self._plotfillers2[i]
        # for i, x in enumerate(self._plotfillers2)}

        figs = []
        for stratlist in self.runstrats:
            for si, strat in enumerate(stratlist):
                rfig = plotter.plot(strat, figid=si * 100,
                                    numfigs=numfigs, iplot=iplot,
                                    start=start, end=end, use=use)
                # pfillers=pfillers2)

                figs.append(rfig)

            plotter.show()

#code from backtrader.Plot.plot is below
def plot(self, strategy, figid=0, numfigs=1, iplot=True,
             start=None, end=None, **kwargs):
        # pfillers={}):
        if not strategy.datas:
            return

        if not len(strategy):
            return

        if iplot:
            if 'ipykernel' in sys.modules:
                matplotlib.use('nbagg')

        # this import must not happen before matplotlib.use
        import matplotlib.pyplot as mpyplot
        self.mpyplot = mpyplot

        self.pinf = PInfo(self.p.scheme)
        self.sortdataindicators(strategy)
        self.calcrows(strategy)

        st_dtime = strategy.lines.datetime.plot()
        if start is None:
            start = 0
        if end is None:
            end = len(st_dtime)

        if isinstance(start, datetime.date):
            start = bisect.bisect_left(st_dtime, date2num(start))

        if isinstance(end, datetime.date):
            end = bisect.bisect_right(st_dtime, date2num(end))

        if end < 0:
            end = len(st_dtime) + 1 + end  # -1 =  len() -2 = len() - 1

        slen = len(st_dtime[start:end])
        d, m = divmod(slen, numfigs)
        pranges = list()
        for i in range(numfigs):
            a = d * i + start
            if i == (numfigs - 1):
                d += m  # add remainder to last stint
            b = a + d

            pranges.append([a, b, d])

        figs = []

        for numfig in range(numfigs):
            # prepare a figure
            fig = self.pinf.newfig(figid, numfig, self.mpyplot)
            figs.append(fig)

            self.pinf.pstart, self.pinf.pend, self.pinf.psize = pranges[numfig]
            self.pinf.xstart = self.pinf.pstart
            self.pinf.xend = self.pinf.pend

            self.pinf.clock = strategy
            self.pinf.xreal = self.pinf.clock.datetime.plot(
                self.pinf.pstart, self.pinf.psize)
            self.pinf.xlen = len(self.pinf.xreal)
            self.pinf.x = list(range(self.pinf.xlen))
            # self.pinf.pfillers = {None: []}
            # for key, val in pfillers.items():
            #     pfstart = bisect.bisect_left(val, self.pinf.pstart)
            #     pfend = bisect.bisect_right(val, self.pinf.pend)
            #     self.pinf.pfillers[key] = val[pfstart:pfend]

            # Do the plotting
            # Things that go always at the top (observers)
            self.pinf.xdata = self.pinf.x
            for ptop in self.dplotstop:
                self.plotind(None, ptop, subinds=self.dplotsover[ptop])

            # Create the rest on a per data basis
            dt0, dt1 = self.pinf.xreal[0], self.pinf.xreal[-1]
            for data in strategy.datas:
                if not data.plotinfo.plot:
                    continue

                self.pinf.xdata = self.pinf.x
                xd = data.datetime.plotrange(self.pinf.xstart, self.pinf.xend)
                if len(xd) < self.pinf.xlen:
                    self.pinf.xdata = xdata = []
                    xreal = self.pinf.xreal
                    dts = data.datetime.plot()
                    xtemp = list()
                    for dt in (x for x in dts if dt0 <= x <= dt1):
                        dtidx = bisect.bisect_left(xreal, dt)
                        xdata.append(dtidx)
                        xtemp.append(dt)

                    self.pinf.xstart = bisect.bisect_left(dts, xtemp[0])
                    self.pinf.xend = bisect.bisect_right(dts, xtemp[-1])

                for ind in self.dplotsup[data]:
                    self.plotind(
                        data,
                        ind,
                        subinds=self.dplotsover[ind],
                        upinds=self.dplotsup[ind],
                        downinds=self.dplotsdown[ind])

                self.plotdata(data, self.dplotsover[data])

                for ind in self.dplotsdown[data]:
                    self.plotind(
                        data,
                        ind,
                        subinds=self.dplotsover[ind],
                        upinds=self.dplotsup[ind],
                        downinds=self.dplotsdown[ind])

            cursor = MultiCursor(
                fig.canvas, list(self.pinf.daxis.values()),
                useblit=True,
                horizOn=True, vertOn=True,
                horizMulti=False, vertMulti=True,
                horizShared=True, vertShared=False,
                color='black', lw=1, ls=':')

            self.pinf.cursors.append(cursor)

            # Put the subplots as indicated by hspace
            fig.subplots_adjust(hspace=self.pinf.sch.plotdist,
                                top=0.98, left=0.05, bottom=0.05, right=0.95)

            laxis = list(self.pinf.daxis.values())

            # Find last axis which is not a twinx (date locator fails there)
            i = -1
            while True:
                lastax = laxis[i]
                if lastax not in self.pinf.vaxis:
                    break

                i -= 1

            self.setlocators(lastax)  # place the locators/fmts

            # Applying fig.autofmt_xdate if the data axis is the last one
            # breaks the presentation of the date labels. why?
            # Applying the manual rotation with setp cures the problem
            # but the labels from all axis but the last have to be hidden
            for ax in laxis:
                self.mpyplot.setp(ax.get_xticklabels(), visible=False)

            self.mpyplot.setp(lastax.get_xticklabels(), visible=True,
                              rotation=self.pinf.sch.tickrotation)

            # Things must be tight along the x axis (to fill both ends)
            axtight = 'x' if not self.pinf.sch.ytight else 'both'
            self.mpyplot.autoscale(enable=True, axis=axtight, tight=True)

        return figs


if __name__ == '__main__':
    main()
    












#code from backtrader.cerebro.plot is below
def plot(self, plotter=None, numfigs=1, iplot=True, start=None, end=None,
             width=16, height=9, dpi=300, tight=True, use=None,
             **kwargs):
        '''
        Plots the strategies inside cerebro

        If ``plotter`` is None a default ``Plot`` instance is created and
        ``kwargs`` are passed to it during instantiation.

        ``numfigs`` split the plot in the indicated number of charts reducing
        chart density if wished

        ``iplot``: if ``True`` and running in a ``notebook`` the charts will be
        displayed inline

        ``use``: set it to the name of the desired matplotlib backend. It will
        take precedence over ``iplot``

        ``start``: An index to the datetime line array of the strategy or a
        ``datetime.date``, ``datetime.datetime`` instance indicating the start
        of the plot

        ``end``: An index to the datetime line array of the strategy or a
        ``datetime.date``, ``datetime.datetime`` instance indicating the end
        of the plot

        ``width``: in inches of the saved figure

        ``height``: in inches of the saved figure

        ``dpi``: quality in dots per inches of the saved figure

        ``tight``: only save actual content and not the frame of the figure
        '''
        if self._exactbars > 0:
            return

        if not plotter:
            from backtrader import plot
            if self.p.oldsync:
                plotter = plot.Plot_OldSync(**kwargs)
            else:
                plotter = plot.Plot(**kwargs)

        # pfillers = {self.datas[i]: self._plotfillers[i]
        # for i, x in enumerate(self._plotfillers)}

        # pfillers2 = {self.datas[i]: self._plotfillers2[i]
        # for i, x in enumerate(self._plotfillers2)}

        figs = []
        for stratlist in self.runstrats:
            for si, strat in enumerate(stratlist):
                rfig = plotter.plot(strat, figid=si * 100,
                                    numfigs=numfigs, iplot=iplot,
                                    start=start, end=end, use=use)
                # pfillers=pfillers2)

                figs.append(rfig)

            plotter.show()

#code from backtrader.Plot.plot is below
def plot(self, strategy, figid=0, numfigs=1, iplot=True,
             start=None, end=None, **kwargs):
        # pfillers={}):
        if not strategy.datas:
            return

        if not len(strategy):
            return

        if iplot:
            if 'ipykernel' in sys.modules:
                matplotlib.use('nbagg')

        # this import must not happen before matplotlib.use
        import matplotlib.pyplot as mpyplot
        self.mpyplot = mpyplot

        self.pinf = PInfo(self.p.scheme)
        self.sortdataindicators(strategy)
        self.calcrows(strategy)

        st_dtime = strategy.lines.datetime.plot()
        if start is None:
            start = 0
        if end is None:
            end = len(st_dtime)

        if isinstance(start, datetime.date):
            start = bisect.bisect_left(st_dtime, date2num(start))

        if isinstance(end, datetime.date):
            end = bisect.bisect_right(st_dtime, date2num(end))

        if end < 0:
            end = len(st_dtime) + 1 + end  # -1 =  len() -2 = len() - 1

        slen = len(st_dtime[start:end])
        d, m = divmod(slen, numfigs)
        pranges = list()
        for i in range(numfigs):
            a = d * i + start
            if i == (numfigs - 1):
                d += m  # add remainder to last stint
            b = a + d

            pranges.append([a, b, d])

        figs = []

        for numfig in range(numfigs):
            # prepare a figure
            fig = self.pinf.newfig(figid, numfig, self.mpyplot)
            figs.append(fig)

            self.pinf.pstart, self.pinf.pend, self.pinf.psize = pranges[numfig]
            self.pinf.xstart = self.pinf.pstart
            self.pinf.xend = self.pinf.pend

            self.pinf.clock = strategy
            self.pinf.xreal = self.pinf.clock.datetime.plot(
                self.pinf.pstart, self.pinf.psize)
            self.pinf.xlen = len(self.pinf.xreal)
            self.pinf.x = list(range(self.pinf.xlen))
            # self.pinf.pfillers = {None: []}
            # for key, val in pfillers.items():
            #     pfstart = bisect.bisect_left(val, self.pinf.pstart)
            #     pfend = bisect.bisect_right(val, self.pinf.pend)
            #     self.pinf.pfillers[key] = val[pfstart:pfend]

            # Do the plotting
            # Things that go always at the top (observers)
            self.pinf.xdata = self.pinf.x
            for ptop in self.dplotstop:
                self.plotind(None, ptop, subinds=self.dplotsover[ptop])

            # Create the rest on a per data basis
            dt0, dt1 = self.pinf.xreal[0], self.pinf.xreal[-1]
            for data in strategy.datas:
                if not data.plotinfo.plot:
                    continue

                self.pinf.xdata = self.pinf.x
                xd = data.datetime.plotrange(self.pinf.xstart, self.pinf.xend)
                if len(xd) < self.pinf.xlen:
                    self.pinf.xdata = xdata = []
                    xreal = self.pinf.xreal
                    dts = data.datetime.plot()
                    xtemp = list()
                    for dt in (x for x in dts if dt0 <= x <= dt1):
                        dtidx = bisect.bisect_left(xreal, dt)
                        xdata.append(dtidx)
                        xtemp.append(dt)

                    self.pinf.xstart = bisect.bisect_left(dts, xtemp[0])
                    self.pinf.xend = bisect.bisect_right(dts, xtemp[-1])

                for ind in self.dplotsup[data]:
                    self.plotind(
                        data,
                        ind,
                        subinds=self.dplotsover[ind],
                        upinds=self.dplotsup[ind],
                        downinds=self.dplotsdown[ind])

                self.plotdata(data, self.dplotsover[data])

                for ind in self.dplotsdown[data]:
                    self.plotind(
                        data,
                        ind,
                        subinds=self.dplotsover[ind],
                        upinds=self.dplotsup[ind],
                        downinds=self.dplotsdown[ind])

            cursor = MultiCursor(
                fig.canvas, list(self.pinf.daxis.values()),
                useblit=True,
                horizOn=True, vertOn=True,
                horizMulti=False, vertMulti=True,
                horizShared=True, vertShared=False,
                color='black', lw=1, ls=':')

            self.pinf.cursors.append(cursor)

            # Put the subplots as indicated by hspace
            fig.subplots_adjust(hspace=self.pinf.sch.plotdist,
                                top=0.98, left=0.05, bottom=0.05, right=0.95)

            laxis = list(self.pinf.daxis.values())

            # Find last axis which is not a twinx (date locator fails there)
            i = -1
            while True:
                lastax = laxis[i]
                if lastax not in self.pinf.vaxis:
                    break

                i -= 1

            self.setlocators(lastax)  # place the locators/fmts

            # Applying fig.autofmt_xdate if the data axis is the last one
            # breaks the presentation of the date labels. why?
            # Applying the manual rotation with setp cures the problem
            # but the labels from all axis but the last have to be hidden
            for ax in laxis:
                self.mpyplot.setp(ax.get_xticklabels(), visible=False)

            self.mpyplot.setp(lastax.get_xticklabels(), visible=True,
                              rotation=self.pinf.sch.tickrotation)

            # Things must be tight along the x axis (to fill both ends)
            axtight = 'x' if not self.pinf.sch.ytight else 'both'
            self.mpyplot.autoscale(enable=True, axis=axtight, tight=True)

        return figs


#code from backtrader.cerebro.plot is below
def plot(self, plotter=None, numfigs=1, iplot=True, start=None, end=None,
             width=16, height=9, dpi=300, tight=True, use=None,
             **kwargs):
        '''
        Plots the strategies inside cerebro

        If ``plotter`` is None a default ``Plot`` instance is created and
        ``kwargs`` are passed to it during instantiation.

        ``numfigs`` split the plot in the indicated number of charts reducing
        chart density if wished

        ``iplot``: if ``True`` and running in a ``notebook`` the charts will be
        displayed inline

        ``use``: set it to the name of the desired matplotlib backend. It will
        take precedence over ``iplot``

        ``start``: An index to the datetime line array of the strategy or a
        ``datetime.date``, ``datetime.datetime`` instance indicating the start
        of the plot

        ``end``: An index to the datetime line array of the strategy or a
        ``datetime.date``, ``datetime.datetime`` instance indicating the end
        of the plot

        ``width``: in inches of the saved figure

        ``height``: in inches of the saved figure

        ``dpi``: quality in dots per inches of the saved figure

        ``tight``: only save actual content and not the frame of the figure
        '''
        if self._exactbars > 0:
            return

        if not plotter:
            from backtrader import plot
            if self.p.oldsync:
                plotter = plot.Plot_OldSync(**kwargs)
            else:
                plotter = plot.Plot(**kwargs)

        # pfillers = {self.datas[i]: self._plotfillers[i]
        # for i, x in enumerate(self._plotfillers)}

        # pfillers2 = {self.datas[i]: self._plotfillers2[i]
        # for i, x in enumerate(self._plotfillers2)}

        figs = []
        for stratlist in self.runstrats:
            for si, strat in enumerate(stratlist):
                rfig = plotter.plot(strat, figid=si * 100,
                                    numfigs=numfigs, iplot=iplot,
                                    start=start, end=end, use=use)
                # pfillers=pfillers2)

                figs.append(rfig)

            plotter.show()

#code from backtrader.Plot.plot is below
def plot(self, strategy, figid=0, numfigs=1, iplot=True,
             start=None, end=None, **kwargs):
        # pfillers={}):
        if not strategy.datas:
            return

        if not len(strategy):
            return

        if iplot:
            if 'ipykernel' in sys.modules:
                matplotlib.use('nbagg')

        # this import must not happen before matplotlib.use
        import matplotlib.pyplot as mpyplot
        self.mpyplot = mpyplot

        self.pinf = PInfo(self.p.scheme)
        self.sortdataindicators(strategy)
        self.calcrows(strategy)

        st_dtime = strategy.lines.datetime.plot()
        if start is None:
            start = 0
        if end is None:
            end = len(st_dtime)

        if isinstance(start, datetime.date):
            start = bisect.bisect_left(st_dtime, date2num(start))

        if isinstance(end, datetime.date):
            end = bisect.bisect_right(st_dtime, date2num(end))

        if end < 0:
            end = len(st_dtime) + 1 + end  # -1 =  len() -2 = len() - 1

        slen = len(st_dtime[start:end])
        d, m = divmod(slen, numfigs)
        pranges = list()
        for i in range(numfigs):
            a = d * i + start
            if i == (numfigs - 1):
                d += m  # add remainder to last stint
            b = a + d

            pranges.append([a, b, d])

        figs = []

        for numfig in range(numfigs):
            # prepare a figure
            fig = self.pinf.newfig(figid, numfig, self.mpyplot)
            figs.append(fig)

            self.pinf.pstart, self.pinf.pend, self.pinf.psize = pranges[numfig]
            self.pinf.xstart = self.pinf.pstart
            self.pinf.xend = self.pinf.pend

            self.pinf.clock = strategy
            self.pinf.xreal = self.pinf.clock.datetime.plot(
                self.pinf.pstart, self.pinf.psize)
            self.pinf.xlen = len(self.pinf.xreal)
            self.pinf.x = list(range(self.pinf.xlen))

            # Do the plotting
            # Things that go always at the top (observers)
            self.pinf.xdata = self.pinf.x
            for ptop in self.dplotstop:
                self.plotind(None, ptop, subinds=self.dplotsover[ptop])

            # Create the rest on a per data basis
            dt0, dt1 = self.pinf.xreal[0], self.pinf.xreal[-1]
            for data in strategy.datas:
                if not data.plotinfo.plot:
                    continue

                self.pinf.xdata = self.pinf.x
                xd = data.datetime.plotrange(self.pinf.xstart, self.pinf.xend)
                if len(xd) < self.pinf.xlen:
                    self.pinf.xdata = xdata = []
                    xreal = self.pinf.xreal
                    dts = data.datetime.plot()
                    xtemp = list()
                    for dt in (x for x in dts if dt0 <= x <= dt1):
                        dtidx = bisect.bisect_left(xreal, dt)
                        xdata.append(dtidx)
                        xtemp.append(dt)

                    self.pinf.xstart = bisect.bisect_left(dts, xtemp[0])
                    self.pinf.xend = bisect.bisect_right(dts, xtemp[-1])

                for ind in self.dplotsup[data]:
                    self.plotind(
                        data,
                        ind,
                        subinds=self.dplotsover[ind],
                        upinds=self.dplotsup[ind],
                        downinds=self.dplotsdown[ind])

                self.plotdata(data, self.dplotsover[data])

                for ind in self.dplotsdown[data]:
                    self.plotind(
                        data,
                        ind,
                        subinds=self.dplotsover[ind],
                        upinds=self.dplotsup[ind],
                        downinds=self.dplotsdown[ind])

            cursor = MultiCursor(
                fig.canvas, list(self.pinf.daxis.values()),
                useblit=True,
                horizOn=True, vertOn=True,
                horizMulti=False, vertMulti=True,
                horizShared=True, vertShared=False,
                color='black', lw=1, ls=':')

            self.pinf.cursors.append(cursor)

            # Put the subplots as indicated by hspace
            fig.subplots_adjust(hspace=self.pinf.sch.plotdist,
                                top=0.98, left=0.05, bottom=0.05, right=0.95)

            laxis = list(self.pinf.daxis.values())

            # Find last axis which is not a twinx (date locator fails there)
            i = -1
            while True:
                lastax = laxis[i]
                if lastax not in self.pinf.vaxis:
                    break

                i -= 1

            self.setlocators(lastax)  # place the locators/fmts

            # Applying fig.autofmt_xdate if the data axis is the last one
            # breaks the presentation of the date labels. why?
            # Applying the manual rotation with setp cures the problem
            # but the labels from all axis but the last have to be hidden
            for ax in laxis:
                self.mpyplot.setp(ax.get_xticklabels(), visible=False)

            self.mpyplot.setp(lastax.get_xticklabels(), visible=True,
                              rotation=self.pinf.sch.tickrotation)

            # Things must be tight along the x axis (to fill both ends)
            axtight = 'x' if not self.pinf.sch.ytight else 'both'
            self.mpyplot.autoscale(
                enable=True, axis=axtight, tight=True)

        return figs

    # def sortdataindicators(self, strategy):
    #     # These lists/dictionaries hold the subplots that go above each data
    #     self.dplotstop = list()
    #     self.dplotsup = collections.defaultdict(list)
    #     self.dplotsdown = collections.defaultdict(list)
    #     self.dplotsover = collections.defaultdict(list)

    #     # Sort observers in the different lists/dictionaries
    #     for x in strategy.getobservers():
    #         if not x.plotinfo.plot or x.plotinfo.plotskip:
    #             continue

    #         if x.plotinfo.subplot:
    #             self.dplotstop.append(x)
    #         else:
    #             key = getattr(x._clock, 'owner', x._clock)
    #             self.dplotsover[key].append(x)

    #     # Sort indicators in the different lists/dictionaries
    #     for x in strategy.getindicators():
    #         if not hasattr(x, 'plotinfo'):
    #             # no plotting support - so far LineSingle derived classes
    #             continue

    #         if not x.plotinfo.plot or x.plotinfo.plotskip:
    #             continue

    #         x._plotinit()  # will be plotted ... call its init function

    #         # support LineSeriesStub which has "owner" to point to the data
    #         key = getattr(x._clock, 'owner', x._clock)
    #         if key is strategy:  # a LinesCoupler
    #             key = strategy.data

    #         if getattr(x.plotinfo, 'plotforce', False):
    #             if key not in strategy.datas:
    #                 datas = strategy.datas
    #                 while True:
    #                     if key not in strategy.datas:
    #                         key = key._clock
    #                     else:
    #                         break

    #         xpmaster = x.plotinfo.plotmaster
    #         if xpmaster is x:
    #             xpmaster = None
    #         if xpmaster is not None:
    #             key = xpmaster

    #         if x.plotinfo.subplot and xpmaster is None:
    #             if x.plotinfo.plotabove:
    #                 self.dplotsup[key].append(x)
    #             else:
    #                 self.dplotsdown[key].append(x)
    #         else:
    #             self.dplotsover[key].append(x)
