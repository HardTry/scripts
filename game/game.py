from libnrlib import *
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import sys
import gc
from scipy import stats
import re
from matplotlib import rcParams

min_data_size = int(102400 * 1.000005)
# min_data_size = int(102400 * 1.05)
predict_len = 128

margin = dict({'CF': 0.07, 'FG': 0.06, 'MA': 0.05, 'OI': 0.05, 'RM': 0.05, 'SR': 0.06, 'TA': 0.06, 'ZC': 0.05, 'a': 0.05, 'ag': 0.07, 'al': 0.05, 'au': 0.07, 'bu': 0.04, 'c': 0.05, 'cu': 0.05, 'i': 0.05, 'j': 0.05, 'jd': 0.05, 'jm': 0.05, 'l': 0.05, 'm': 0.05, 'ni': 0.05, 'p': 0.05, 'pb': 0.07, 'pp': 0.05, 'rb': 0.07, 'ru': 0.05, 'v': 0.05, 'y': 0.05, 'zn': 0.05})
unit = dict({'CF': 5, 'FG': 20, 'MA': 10, 'OI': 10, 'RM': 10, 'SR': 10, 'TA': 5, 'ZC': 100, 'a': 10, 'ag': 15, 'al': 5, 'au': 1000, 'bu': 10, 'c': 10, 'cu': 5, 'i': 100, 'j': 100, 'jd': 10, 'jm': 60, 'l': 10, 'm': 10, 'ni': 1, 'p': 10, 'pb': 5, 'pp': 5, 'rb': 10, 'ru': 10, 'v': 5, 'y': 10, 'zn': 5})
hop = dict({'CF': 5, 'FG': 1, 'MA': 1, 'OI': 2, 'RM': 1, 'SR': 1, 'TA': 2, 'ZC': 2, 'a': 1, 'ag': 1, 'al': 5, 'au': 5, 'bu': 2, 'c': 1, 'cu': 10, 'i': 5, 'j': 5, 'jd': 1, 'jm': 5, 'l': 5, 'm': 1, 'ni': 10, 'p': 2, 'pb': 5, 'pp': 1, 'rb': 1, 'ru': 5, 'v': 5, 'y': 2, 'zn': 5})

commision = 0.00005

my_unit = 10
my_margin = 0.05
my_hop = 1

def get_instrument_code(inst):
    global my_unit, my_margin, my_hop
    match = re.match(r"([a-z]+)([0-9]+)", inst, re.I)
    code = ''
    if match:
        items = match.groups()
        code = items[0]
        my_unit = unit[code]
        my_margin = margin[code]
        my_hop = hop[code]
    return code


class Order:
    def __init__(self):
        self.direct = ''
        self.pos_ = 0
        self.price = 0
        self.posrev = 0
        self.rev = 0
        self.inst = ''
        self.margin = 0.0
        self.unit = 0.0

    def __init__(self, direct, pos, price):
        self.direct = direct
        self.pos_ = pos
        self.price = price
        self.posrev = 0  # current revenue
        self.rev = 0  # revenue
        self.inst = ''
        self.margin = 0.0
        self.unit = 0.0


class Trade:
    order = []
    allrev = 0

    def __init__(self, dm):
        self.dm = dm

    def openLong(self, cur_pos):
        if (0 == len(self.order) % 2):
            print 'Long ', cur_pos, self.dm.price[cur_pos]
            self.order.append(Order('a', cur_pos, self.dm.price[cur_pos]))
            return True
        else:
            return False

    def openShort(self, cur_pos):
        if (0 == len(self.order) % 2):
            print 'Short ', cur_pos, self.dm.price[cur_pos]
            self.order.append(Order('b', cur_pos, self.dm.price[cur_pos]))
            return True
        else:
            return False

    def closePosition(self, cur_pos):
        if (1 == len(self.order) % 2):
            c = Order('c', cur_pos, self.dm.price[cur_pos])
            if self.order[-1].direct == 'a':
                c.posrev = (c.price - self.order[-1].price) * my_unit
                c.rev = (c.price - self.order[-1].price) * my_unit \
                        - (c.price + self.order[-1].price) * my_unit * commision
            else:
                c.posrev = (self.order[-1].price - c.price) * my_unit
                c.rev = (self.order[-1].price - c.price) * my_unit \
                        - (c.price + self.order[-1].price) * my_unit * commision
            self.order.append(c)
            self.allrev += c.rev
            print 'Close', cur_pos, self.dm.price[cur_pos], c.posrev, c.rev, self.allrev
            return True
        else:
            return False




def get_data_from_file(instrument, datapath, thedate):
    price = []
    ftime = []


    # ret = load_10s_ts_from_date_v1(instrument, datapath, thedate, min_data_size, price, ftime)
    ret = load_10s_ts_from_date_v2(instrument, datapath, thedate, min_data_size, my_hop, price, ftime)
    if (ret != 0):
        print "error code " + str(ret)

    all_len = len(price)
    allx = list(range(0, all_len + predict_len))
    return ret, price, all_len, allx, thedate


def print_ve(ve):
    for e in ve:
        print e.pos, ", ",
    print


class DataLines:
    def __init__(self):
        self.max_x = []
        self.max_y = []
        self.min_x = []
        self.min_y = []

    def set_data(self, ve, max_x, min_x, cp, prdlen):
        if (len(max_x) > 1 and len(min_x) > 1):
            self.max_x = []
            self.max_y = []
            self.min_x = []
            self.min_y = []

            for x in max_x:
                self.max_x.append(ve[x].pos - ve[max_x[0]].pos)
                self.max_y.append((ve[x].val - ve[max_x[0]].val)/my_hop)
            slope1, intercept, r_value, p_value, std_err = stats.linregress(self.max_x, self.max_y)

            for x in min_x:
                self.min_x.append(ve[x].pos - ve[min_x[0]].pos)
                self.min_y.append((ve[x].val - ve[min_x[0]].val)/my_hop)
            slope2, intercept, r_value, p_value, std_err = stats.linregress(self.min_x, self.min_y)

            self.max_x = []
            self.max_y = []
            self.min_x = []
            self.min_y = []
            la = LinesAttr()
            #int fit_line(const std::vector<NR::Extreme>& ext, const bp::list& imax,
            # const bp::list& imin, const double hop,
            # const int current_pos, const int predict_len,
            # LinesAttr& la, bp::list& max_line, bp::list& min_line)
            fit_line(ve, max_x, min_x, cp, prdlen, la, self.max_y, self.min_y)
            # print slope1, slope2
            # print la.k_max, la.y0_max, la.k_min, la.y0_min
            # print slope1 - la.k_max, slope2 - la.k_min, slope1 - la.k_max < 1e-12, slope2 - la.k_min < 1e-12
            # print max_x[0], cp, prdlen, cp+prdlen
            self.max_x = list(range(ve[max_x[0]].pos, cp + prdlen))
            self.min_x = list(range(ve[min_x[0]].pos, cp + prdlen))
            # print len(self.max_x), len(self.max_y)



class DataMath:
    def __init__(self, price, all_len, allx, the_date):
        self.price = price
        self.all_len = all_len
        self.allx = allx
        self.the_date = the_date

        self.down_int = 1
        self.data_len = 1024
        self.predict_len = 128
        self.lvl_hi = 7
        self.lvl_ma_lo = 10
        self.lvl_ma_mid = 30
        self.lvl_ma_hi = 60

        self.predict = Predict(self.data_len, self.predict_len)
        self.wt = WaveletFilter(1, self.data_len, self.lvl_hi)
        self.ma = MaFilter(self.lvl_ma_lo, self.data_len);

        self.appx_hi_len = self.data_len
        self.appx_hi = []
        self.ap_hi = []
        self.ap_hi_pos = 0

        self.ma_lo = []
        self.ma_mid = []
        self.ma_hi = []

        self.ext_pos = []
        self.ext_val = []
        self.first_ext_pos = 0
        self.ve = VectorExtreme()

        self.veAppx = VectorExtreme()
        self.ext_appx_pos = []
        self.ext_appx_val = []

        self.dl = DataLines()

    def down_sample(self, down_int):
        self.down_int = down_int / 2
        # plt.plot(list(range(0, len(self.price))), self.price)
        # plt.show()
	# print self.price[182000:185201:200]
        self.price = sample_max_min(self.price, down_int)
        # plt.plot(list(range(0, len(self.price))), self.price)
        # plt.show()
        self.all_len = len(self.price)
        self.allx = list(range(0, self.all_len + self.predict_len))

    def do_math(self, cp):
        # print cp, self.all_len
        self.ma.set(self.lvl_ma_lo, self.data_len)
        self.ma.setdata(self.price[cp - self.data_len: cp])
        self.ma_lo = self.ma.filter()

        self.ma.set(self.lvl_ma_mid, self.data_len)
        self.ma_mid = self.ma.filter()

        self.ma.set(self.lvl_ma_hi, self.data_len)
        self.ma_hi = self.ma.filter()

        self.ext_val = []
        self.ext_pos = []
        self.ve = get_sample_extreme(self.price[cp - self.data_len: cp], 50, cp - self.data_len, \
                                     self.ext_pos, self.ext_val)
        self.first_ext_pos = self.ext_pos[-1]

        pos = 0
        if (self.first_ext_pos - self.data_len < 0):
            self.appx_hi_len = self.first_ext_pos
        else:
            self.appx_hi_len = self.data_len
            pos = self.first_ext_pos - self.data_len

        self.wt.set(1, self.appx_hi_len, self.lvl_hi)
        self.wt.setdata(self.price[pos: self.first_ext_pos])
        self.appx_hi = self.wt.filter()

        self.ap_hi_pos = self.first_ext_pos
        self.predict.setdata(self.appx_hi)
        self.ap_hi = self.predict.predict()

        pa = PredictAttr()
        find_predict_extreme(self.ap_hi, pa)
        # print cp, pa.type, pa.slope_1, pa.slope_2

        self.ext_appx_pos = []
        self.ext_appx_val = []

        self.veAppx = get_appx_org_extreme(self.appx_hi + self.ap_hi, \
                                           self.ve, \
                                           cp - self.data_len, \
                                           self.ext_appx_pos, \
                                           self.ext_appx_val)
        # print self.ext_appx_pos

        pricemax = []
        pricemin = []
        # print "math ", self.down_int, " ve ",
        # print_ve(self.ve)
        # print "math ", self.down_int, " veappx ",
        # print_ve(self.veAppx)
        get_last_slice(self.ve, self.veAppx, pricemax, pricemin)
        # print pricemax, pricemin
        self.dl.set_data(self.ve, pricemax, pricemin, cp, self.predict_len)


class ArtistTrade:
    def __init__(self, trade, dm, ax, name):
        self.trade = trade
        self.dm = dm
        self.name = name
        self.ax = ax

        self.ax.set_xlim([0, 100])
        self.ax.set_ylim([0, 100])

        self.txtTrade = self.ax.text(-1000, 8, 'text ask', fontsize=9, color='red')
        self.txtRev = self.ax.text(-1000, 8, 'text rev', fontsize=9, color='black')
        self.txtAllRev = self.ax.text(-1000, 8, 'text all rev', fontsize=9, color='black')

    def set_trade(self, trade):
        self.trade = trade

    def update_revenue(self, cur_pos):
        rev = 0

        self.txtTrade.set_position((10, 3))
        if (1 == len(self.trade.order) % 2):
            if self.trade.order[-1].direct == 'a':
                rev = (self.dm.price[cur_pos] - self.trade.order[-1].price) * my_unit\
                      - ((self.dm.price[cur_pos] + self.trade.order[-1].price) * my_unit * commision)
                self.txtTrade.set_color('red')
                self.txtTrade.set_text('Long')
            else:
                rev = (self.trade.order[-1].price - self.dm.price[cur_pos]) * my_unit\
                      - ((self.dm.price[cur_pos] + self.trade.order[-1].price) * my_unit * commision)
                self.txtTrade.set_color('green')
                self.txtTrade.set_text('Short')
        else:
            self.txtTrade.set_text('')

        self.txtRev.set_position((10, 3 + 10))
        if rev == 0:
            str_rev = ''
        else:
            str_rev = str(rev)

        if (rev > 0):
            self.txtRev.set_color('red')
        else:
            self.txtRev.set_color('green')
        self.txtRev.set_text(str_rev)

        self.txtAllRev.set_position((10, 3 + 20))
        if (self.trade.allrev == 0):
            str_all_rev = ''
        else:
            str_all_rev = str(self.trade.allrev)
        if (self.trade.allrev > 0):
            self.txtAllRev.set_color('red')
        else:
            self.txtAllRev.set_color('green')
        self.txtAllRev.set_text(str_all_rev)

    def animate(self, cur_pos):
        # print self.name, " : ", cur_pos
        # print self.name, cur_pos, pass_pos, its_review, show_future

        self.update_revenue(cur_pos)

        '''
        TODO: Add your trade algorithm HERE!
        '''

        return (self.txtTrade, self.txtRev, self.txtAllRev)


class Artist:
    def __init__(self, dm, ax, name):
        self.dm = dm
        self.name = name
        self.ax = ax

        self.ax.set_xlim([0, dm.data_len + dm.predict_len])
        self.ax.set_ylim([min(dm.price[0: dm.data_len]),
                          max(dm.price[0: dm.data_len])])

        # self.lPassed, = self.ax.plot([], [], lw=1, color='black')
        self.lCurrent, = self.ax.plot([], [], lw=1, color='blue')
        self.lFuture, = self.ax.plot([], [], lw=1, color='green')
        # self.lma_hi, = self.ax.plot([], [], lw=1, color='yellow')
        # self.lma_lo, = self.ax.plot([], [], lw=1, color='pink')
        # self.lma_mid, = self.ax.plot([], [], lw=1, color='black')
        self.lp_hi, = self.ax.plot([], [], lw=1, color='red')
        self.lExtrem, = self.ax.plot([], [], 'rx', lw=1)  # lw=2, color='black', marker='o', markeredgecolor='b')
        self.lExtremAppx, = self.ax.plot([], [], 'yo', lw=1)  # lw=2, color='black', marker='o', markeredgecolor='b')
        self.lNow, = self.ax.plot([], [], lw=1, color='green')
        self.lmax, = self.ax.plot([], [], lw = 1, color = 'black')
        self.lmin, = self.ax.plot([], [], lw = 1, color = 'black')

        self.down_int = 1

        self.lines = [self.lCurrent, self.lFuture, self.lp_hi, self.lExtrem, self.lExtremAppx, self.lNow, self.lmax, self.lmin]


    def init_animation(self):
        for line in self.lines:
            line.set_data([], [])
        return self.lines

    def set_dm_int(self, down_int):
        self.down_int = down_int
        self.ax.set_xlim([0, self.dm.data_len + self.dm.predict_len])
        self.ax.set_ylim([min(self.dm.price[0: self.dm.data_len]),
                          max(self.dm.price[0: self.dm.data_len])])

    def update_limite(self, xlim, ylim, cp):
        delta = cp + self.dm.predict_len - xlim[1]
        if delta > 0:
            xlim[0] = cp - self.dm.data_len
            xlim[1] = cp + self.dm.predict_len
        self.ax.set_xlim(xlim)
        
        self.ax.set_ylim([min(self.dm.price[int(xlim[0]): int(xlim[1])]),\
                          max(self.dm.price[int(xlim[0]): int(xlim[1])])])
    def update_lines(self, xlim, cp, pp, its_review, show_future):
        self.lCurrent.set_data(self.dm.allx[cp - self.dm.data_len: cp],
                               self.dm.price[cp - self.dm.data_len: cp])
        self.update_extreme_appx(cp)
        self.update_extreme_lo(cp)

        # self.lma_lo.set_data(self.dm.allx[cp - self.dm.data_len: cp], self.dm.ma_lo)
        # self.lma_mid.set_data(self.dm.allx[self.dm.first_ext_pos - len(self.dm.appx_hi): \
        #                       self.dm.first_ext_pos], \
        #                       self.dm.appx_hi)
        # self.lma_hi.set_data(self.dm.allx[cp - self.dm.data_len: cp], self.dm.ma_hi)

        if show_future:
            dlen = len(self.dm.price[cp: cp + self.dm.predict_len])
            self.lFuture.set_data(self.dm.allx[cp: cp + dlen], \
                                  self.dm.price[cp: cp + self.dm.predict_len])
        else:
            self.lFuture.set_data([], [])

        self.lNow.set_data([self.dm.first_ext_pos, cp], \
                           [self.dm.price[self.dm.first_ext_pos], self.dm.price[cp]])

        # print 4, len(self.dm.allx[self.dm.ap_hi_pos: self.dm.ap_hi_pos + self.dm.predict_len]), len(self.dm.ap_hi)
        l = len(self.dm.allx[self.dm.ap_hi_pos: self.dm.ap_hi_pos + self.dm.predict_len])
        self.lp_hi.set_data(self.dm.allx[self.dm.ap_hi_pos: self.dm.ap_hi_pos + self.dm.predict_len], \
                            self.dm.ap_hi[0: l])

        self.lmax.set_data(self.dm.dl.max_x, self.dm.dl.max_y)
        self.lmin.set_data(self.dm.dl.min_x, self.dm.dl.min_y)


    def update_extreme_lo(self, cp):
        # print self.name, cp, len(self.dm.ext_pos)
        self.lExtrem.set_data(self.dm.ext_pos, self.dm.ext_val)

    def update_extreme_appx(self, cp):
        self.lExtremAppx.set_data(self.dm.ext_appx_pos, self.dm.ext_appx_val)

    def animate(self, cur_pos, pass_pos, its_review, show_future):
        cp = cur_pos / self.down_int
        pp = pass_pos / self.down_int
        #
        # if (cp + self.dm.predict_len > self.dm.all_len):
        #     return
        #
        xlim = list(self.ax.get_xlim())
        ylim = list(self.ax.get_ylim())
        #
        self.update_limite(xlim, ylim, cp)
        #
        self.dm.do_math(cp)

        self.update_lines(xlim, cp, pp, its_review, show_future)

        return tuple(self.lines)


class SubplotAnimation(animation.TimedAnimation):
    def __init__(self, dm1, dm2, dm3):
        self.fig = plt.figure()
        self.ax1 = self.fig.add_subplot(2, 2, 1)
        self.ax2 = self.fig.add_subplot(2, 2, 2)
        self.ax3 = self.fig.add_subplot(2, 2, 3)
        self.ax4 = self.fig.add_subplot(2, 2, 4)
        self.dm1 = dm1
        self.dm2 = dm2
        self.dm3 = dm3

        self.trade = Trade(dm1)

        self.art1 = Artist(dm1, self.ax1, "art1")

        self.art2 = Artist(dm2, self.ax2, "art2")
        self.art2.set_dm_int(dm2.down_int)

        self.art3 = Artist(dm3, self.ax3, "art3")
        self.art3.set_dm_int(dm3.down_int)

        self.art4 = ArtistTrade(self.trade, dm1, self.ax4, "art4")

        self.anim_running = True
        self.anim_interval = 0  # 500

        self.cur_pos = dm1.data_len
        self.max_curpos = self.cur_pos
        self.pass_pos = 0
        self.show_future = False
        self.its_review = False

        self.fig.canvas.mpl_connect('key_press_event', self.press)
        self.fig.canvas.mpl_connect('close_event', self.handle_close)
        self.fig.canvas.mpl_connect('resize_event', self.on_resize)
        # self.fig.canvas.mpl_connect('button_press_event', self.onClick)
        self.event_source = self.fig.canvas.new_timer()
        self.event_source.interval = self.anim_interval

        animation.TimedAnimation.__init__(self, self.fig, interval=self.anim_interval,
                                          event_source=self.event_source, blit=True)

    # def onClick(self, event):
    #    # print(event.button, event.xdata, event.ydata)
    #    # if (event.button == 3):
    #    self.show_future = not self.show_future

    def on_resize(self, event):
        self.event_source.stop()
        self.anim_running = False

    def handle_close(self, event):
        self.event_source.stop()
        if self.dm1.closePosition(self.cur_pos):
            self.art1.strTrade = ''
            self.art1.strAllRev = str(self.dm1.allrev)
        self.anim_running = False

    def press(self, event):
        # print event.key
        if event.key == 'i':
            if self.anim_running:
                self.event_source.stop()
                self.anim_running = False
            else:
                self.event_source.start()
                self.anim_running = True
        elif event.key == 'a':
            self.trade.openLong(self.cur_pos)
        elif event.key == 'b':
            self.trade.openShort(self.cur_pos)
        elif event.key == 'c':
            self.trade.closePosition(self.cur_pos)
        elif event.key == 'h':
            self.event_source.stop()
            if self.cur_pos - 10 > dm1.data_len:
                self.cur_pos -= 10
                self.its_review = True
            self.event_source.start()
        elif event.key == 'l':
            self.event_source.stop()
            if self.cur_pos + 10 < self.max_curpos:
                self.cur_pos += 8
                self.its_review = True
            self.event_source.start()
        elif event.key == 'e':
            print dm1.the_date, self.cur_pos, " has Error"
        elif event.key == 't':
            self.show_future = not self.show_future
        elif event.key == '=':
            if self.event_source.interval >= 10:
                self.event_source.interval -= 10
        elif event.key == '-':
            if self.event_source.interval <= 300:
                self.event_source.interval += 10

    def _draw_frame(self, framedata):
        if (self.cur_pos > self.max_curpos):
            self.its_review = False

        self._drawn_artists = self.art1.animate(self.cur_pos, self.pass_pos, self.its_review, self.show_future) \
                              + self.art2.animate(self.cur_pos, self.pass_pos, self.its_review, self.show_future) \
                              + self.art3.animate(self.cur_pos, self.pass_pos, self.its_review, self.show_future) \
                              + self.art4.animate(self.cur_pos)

        self.max_curpos = max(self.cur_pos, self.max_curpos)

        self.pass_pos = self.cur_pos - dm1.data_len

        if self.cur_pos < dm1.all_len - dm1.predict_len:
            self.cur_pos += 1

    def new_frame_seq(self):
        return iter(range(dm1.all_len))

    def _init_draw(self):
        self.cur_pos = 1024 * 10 * 10
        self.art1.init_animation()
        self.art2.init_animation()
        self.art3.init_animation()


if __name__ == "__main__":
    gc.disable()
    gc.enable()

    if (len(sys.argv) != 4):
        print 'Usage: python game.py <instrument> <r|the trade day> <data file path>\n' \
              '       1. r means you want a random day\n' \
              '          format of trade day is YYYYMMDD\n' \
              '       2. the data file path tell game where is the store of history data\n' \
              '          For example:\n' \
              '          get random trade-day data\n' \
              '            python game.py rb888 r /data/sean/10s_candle_bindata\n' \
              '          get one day data\n' \
              '            python game.py rb888 20150601 /data/sean/10s_candle_bindata\n\n' \
              '  Keyboard:                              \n' \
              '      i: pause/continue                  \n' \
              '      a: open long                       \n' \
              '      b: open short                      \n' \
              '      c: close current position          \n' \
              '      h: go back 10 datas                \n' \
              '      l: go forward 10 datas             \n' \
              '      e: show error in console           \n' \
              '      t: toggle to show/hiden future data\n' \
              '      =: accelatate the play speed       \n' \
              '      -: make the play speed slow down   \n'
    else:
        # price, all_ask, all_bid, all_len, allx, the_date = get_data()
        instrument = sys.argv[1].encode('ascii')
        thedate = sys.argv[2].encode('ascii');
        datapath = sys.argv[3].encode('ascii') + '/' + instrument


        get_instrument_code(instrument)

        ret, price, all_len, allx, the_date = get_data_from_file(instrument, datapath, thedate)
	# plt.plot(list(range(0, all_len)), price)
	# plt.show()
        if (ret == 0) and (all_len >= min_data_size):
            dm1 = DataMath(price, all_len, allx, the_date)
            dm2 = DataMath(price, all_len, allx, the_date)
            dm2.down_sample(20)
            dm3 = DataMath(price, all_len, allx, the_date)
            dm3.down_sample(200)
            # print dm1.all_len, dm2.all_len, dm3.all_len

            opq = str(raw_input("enter something to draw: (q = quit)"))
            if (opq == 'q'):
                exit(0)

            rc_params = {'legend.fontsize': 'small',
                         'figure.figsize': (16, 9),
                         'axes.labelsize': 'small',
                         'axes.titlesize': 'small',
                         'xtick.labelsize': 'small',
                         'ytick.labelsize': 'small'}

            for key, value in sorted(rc_params.iteritems()):
                rcParams[key] = value

            ani = SubplotAnimation(dm1, dm2, dm3)
            # ani.save('test_sub.mp4')
            plt.show()

