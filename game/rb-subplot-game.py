from mongoengine import *
import random
from libnrlib import *
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import sys


class Order:
    def __init__(self):
        self.direct = ''
        self.pos_ = 0
        self.price = 0
        self.posrev = 0
        self.rev = 0

    def __init__(self, direct, pos, price):
        self.direct = direct
        self.pos_ = pos
        self.price = price
        self.posrev = 0 #current revenue
        self.rev = 0    #revenue


class Trade:
    order = []
    allrev = 0

    def __init__(self, dm):
        self.dm = dm


    def openLong(self, cur_pos):
        if (0 == len(self.order) % 2):
            print 'Long ', cur_pos, self.dm.all_ask[cur_pos]
            self.order.append(Order('a', cur_pos, self.dm.all_ask[cur_pos]))
            return True
        else:
            return False


    def openShort(self, cur_pos):
        if (0 == len(self.order) % 2):
            print 'Short ', cur_pos, self.dm.all_ask[cur_pos]
            self.order.append(Order('b', cur_pos, self.dm.all_bid[cur_pos]))
            return True
        else:
            return False


    def closePosition(self, cur_pos):
        if (1 == len(self.order) % 2):
            c = Order('c', cur_pos, self.dm.all_data[cur_pos])
            if self.order[-1].direct == 'a':
                c.posrev = (c.price - self.order[-1].price) * 10
                c.rev = (c.price - self.order[-1].price) * 10\
                        - (c.price + self.order[-1].price) * 0.0015
            else:
                c.posrev = (self.order[-1].price - c.price) * 10
                c.rev = (self.order[-1].price - c.price) * 10\
                        - (c.price + self.order[-1].price) * 0.0015
            self.order.append(c)
            self.allrev += c.rev
            print 'Close', cur_pos, self.dm.all_data[cur_pos], c.posrev, c.rev, self.allrev
            return True
        else:
            return False



class Tick(Document):
    askVolume1 = FloatField()
    lastPrice = FloatField()
    askPrice1 = FloatField()
    bidPrice1 = FloatField()
    strDate = StringField()
    Volume = FloatField()
    instrument = StringField()
    bidVolume1 = FloatField()
    openInterest = FloatField()
    strTime = StringField()
    fltTime = FloatField()

    meta = {
        'collection': 'tickdata'
    }


def get_data():
    register_connection("ctpdata", host='10.10.10.13', port=29875)
    conn = connect(db="ctpdata", host='10.10.10.13', port=29875)
    tdays = Tick.objects(instrument='rb888').distinct("strDate")

    pos = random.randrange(30, len(tdays) - 30)
    sd = pos - 30

    all_len = 0
    all_data = []
    all_ask = []
    all_bid = []
    while(sd <= pos and all_len < 20480):
        prev_ticks = Tick.objects(instrument='rb888', strDate=tdays[sd])
        l = []
        a = []
        b = []
        for tick in prev_ticks:
            l.append(tick.lastPrice)
            a.append(tick.askPrice1)
            b.append(tick.bidPrice1)

        all_data += sample_max_min(l, 20)
        all_ask += sample_max_min(a, 20)
        all_bid += sample_max_min(b, 20)

        all_len = len(all_data)
        print tdays[sd], len(prev_ticks), all_len

        sd += 1


    conn.close()

    all_len = len(all_data)

    # print "all len is ", all_len
    allx = list(range(0, all_len))
    return all_data, all_ask, all_bid, all_len, allx, tdays[pos]


def get_data_from_file(argv):
    last = []
    ask = []
    bid = []

    ret = load_trade_datay(argv[1].encode('ascii'), argv[2].encode('ascii'), 20, 20480, last, ask, bid)
    if (ret != 0):
        print "error code " + ret

    all_len = len(last)
    allx = list(range(0, all_len))
    return ret, last, ask, bid, all_len, allx, "random"




class DataMath:
    def __init__(self, all_data, all_ask, all_bid, all_len, allx, the_date):
        self.all_data = all_data
        self.all_ask = all_ask
        self.all_bid = all_bid
        self.all_len = all_len
        self.allx = allx
        self.the_date = the_date

        self.down_int = 1
        self.data_len = 1024
        self.predict_len = 128
        self.lvl_hi = 7
        self.lvl_lo = 4
        self.lvl_mid = 6
        self.predict = Predict(self.data_len, self.predict_len)
        self.wt = WaveletFilter(1, self.data_len, self.lvl_hi)

        self.cur_appx_lo = []
        self.cur_appx_mid = []
        self.cur_appx_spos = self.data_len
        self.cur_appx_epos = self.cur_appx_spos + self.data_len
        self.cur_ext_pos = []
        self.cur_ext_val = []
        self.cur_ext_mid_pos = []
        self.cur_ext_mid_val = []

        self.appx_hi = []
        self.appx_lo = []
        self.appx_mid = []
        self.ap_hi = []
        self.ext_pos = []
        self.ext_val = []
        self.ext_first = 0
        self.ext_mid_pos = []
        self.ext_mid_val = []
        self.ext_mid_first = 0

    def down_sample(self, down_int):
        self.down_int = down_int / 2
        self.all_data = sample_max_min(self.all_data, down_int)
        self.all_ask  = sample_max_min(self.all_ask , down_int)
        self.all_bid  = sample_max_min(self.all_bid , down_int)
        self.all_len  = len(self.all_data)
        self.allx = list(range(0, self.all_len))


    def do_math(self, cp):
        self.wt.setdata(self.all_data[cp - self.data_len: cp])
        self.wt.set(1, self.data_len, self.lvl_hi)
        self.appx_hi = self.wt.filter()

        self.wt.setdata(self.all_data[cp - self.data_len: cp])
        self.wt.set(1, self.data_len, self.lvl_lo)
        self.appx_lo = self.wt.filter()

        self.wt.setdata(self.all_data[cp - self.data_len: cp])
        self.wt.set(1, self.data_len, self.lvl_mid)
        self.appx_mid = self.wt.filter()

        self.predict.setdata(self.appx_hi)
        self.ap_hi = self.predict.predict()

        self.ext_pos = []
        self.ext_val = []
        self.first = get_max_min(self.appx_lo, cp - self.data_len, \
                                 self.ext_pos, self.ext_val)


        self.ext_mid_pos = []
        self.ext_mid_val = []
        self.first = get_max_min(self.appx_mid, cp - self.data_len, \
                                 self.ext_mid_pos, self.ext_mid_val)

        # predict.setdata(appx_lo)
        # ap_lo = predict.predict()

        # return appx_hi, appx_lo, ap_hi, ext_pos, ext_val, first



class Artist:
    def __init__(self, dm, ax, name):
        self.dm = dm
        self.name = name
        self.ax = ax

        self.ax.set_xlim([0, dm.data_len + dm.predict_len])
        self.ax.set_ylim([min(dm.all_data[0: dm.data_len]),
                          max(dm.all_data[0: dm.data_len])])

        self.lPassed,    = self.ax.plot([], [], lw=1, color='black')
        self.lCurrent,   = self.ax.plot([], [], lw=1, color='blue')
        self.lFuture,    = self.ax.plot([], [], lw=1, color='green')
        self.lappx_hi,   = self.ax.plot([], [], lw=1, color='yellow')
        self.lappx_lo,   = self.ax.plot([], [], lw=1, color='pink')
        self.lappx_mid,  = self.ax.plot([], [], lw=1, color='black')
        self.lp_hi,      = self.ax.plot([], [], lw=1, color='red')
        self.lExtrem,    = self.ax.plot([], [], 'rx', lw=1)  # lw=2, color='black', marker='o', markeredgecolor='b')
        self.lExtremMid, = self.ax.plot([], [], 'yo', lw=1)  # lw=2, color='black', marker='o', markeredgecolor='b')
        self.lNow,       = self.ax.plot([], [], lw=1, color='green')

        self.txtTrade    = self.ax.text(-1000, 8, 'text ask', fontsize=9, color='red')
        self.txtRev      = self.ax.text(-1000, 8, 'text rev', fontsize=9, color='black')
        self.txtAllRev   = self.ax.text(-1000, 8, 'text all rev', fontsize=9, color='black')

        self.down_int = 1
        self.trade = Trade

        self.lines = [self.lPassed, self.lCurrent, self.lFuture, self.lappx_hi,\
                      self.lappx_lo, self.lappx_mid, self.lp_hi, self.lExtrem, \
                      self.lExtremMid, self.lNow]  # , lp_lo]


    def init_animation(self):
        for line in self.lines:
            line.set_data([], [])
        return self.lines

    def set_dm_int(self, down_int):
        self.down_int = down_int
        self.ax.set_xlim([0, self.dm.data_len + self.dm.predict_len])
        self.ax.set_ylim([min(self.dm.all_data[0: self.dm.data_len]),
                          max(self.dm.all_data[0: self.dm.data_len])])


    def set_trade(self, trade):
        self.trade = trade

    def update_limite(self, xlim, ylim, cp):
        delta = cp + self.dm.predict_len - xlim[1]
        if delta > 0:
            xlim[0] = cp - self.dm.data_len
            xlim[1] = cp + self.dm.predict_len
        self.ax.set_xlim(xlim)

        ymax = max(self.dm.all_data[int(xlim[0]): cp])
        ymin = min(self.dm.all_data[int(xlim[0]): cp])
        if (ymin < ylim[0]) or (ymin > ylim[0] + 10):
            ylim[0] = ymin - 5
        if (ymax > ylim[1]) or (ymax < ylim[1] - 10):
            ylim[1] = ymax + 5
        self.ax.set_ylim(ylim)


    def update_lines(self, xlim, cp, pp, its_review, show_future):
        if its_review:
            # self.lPassed.set_data(self.dm.allx[int(xlim[0]): pp],
            #                       self.dm.all_data[int(xlim[0]): pp])

            self.lCurrent.set_data(self.dm.allx[cp - self.dm.data_len: cp],
                                   self.dm.all_data[cp - self.dm.data_len: cp])

            if show_future:
                self.lFuture.set_data(self.dm.allx[cp: cp + self.dm.predict_len],\
                                      self.dm.all_data[cp: cp + self.dm.predict_len])

            else:
                self.lFuture.set_data([], [])

                self.lNow.set_data([self.dm.cur_ext_pos[0], cp],\
                                   [self.dm.cur_ext_val[0], self.dm.all_data[cp]])

            self.lappx_hi.set_data(self.dm.allx[cp - self.dm.data_len: cp],\
                                   self.dm.appx_hi)
            self.lappx_lo.set_data(self.dm.allx[cp - self.dm.data_len: cp],\
                                   self.dm.appx_lo)
            self.lappx_mid.set_data(self.dm.allx[cp - self.dm.data_len: cp],\
                                    self.dm.appx_mid)

            self.lp_hi.set_data(self.dm.allx[cp: cp + self.dm.predict_len],
                                self.dm.ap_hi)

            # self.lExtrem.set_data([], [])
        else:
            self.update_extreme_lo(cp)
            self.update_extreme_mid(cp)

            # print self.name, " keep: ", keep
            # print len(self.dm.allx[int(xlim[0]): pass_pos]), len(self.dm.all_data[int(xlim[0]): pass_pos])

            # self.lPassed.set_data(self.dm.allx[int(xlim[0]): pp],
            #                       self.dm.all_data[int(xlim[0]): pp])

            # print len(self.dm.allx[pass_pos: cp]), len(self.dm.all_data[pass_pos: cp])
            self.lCurrent.set_data(self.dm.allx[cp - self.dm.data_len: cp],
                                   self.dm.all_data[cp - self.dm.data_len: cp])

            # print len(self.dm.allx[cp: cp + self.dm.predict_len]),\
            #     len(self.dm.all_data[cp: cp + self.dm.predict_len])
            if show_future:
                self.lFuture.set_data(self.dm.allx[cp: cp + self.dm.predict_len],
                                      self.dm.all_data[cp: cp + self.dm.predict_len])

            else:
                self.lFuture.set_data([], [])

            self.lNow.set_data([self.dm.cur_ext_pos[0], cp], [self.dm.cur_ext_val[0], self.dm.all_data[cp]])

            # print len(self.dm.allx[pass_pos: cp]),\
            #     len(self.dm.appx_hi), len(self.dm.allx[pass_pos: cp]),\
            #     len(self.dm.appx_lo), len(self.dm.allx[cp - self.dm.data_len: cp]),\
            #     len(self.dm.appx_lo)

            self.lappx_lo.set_data(self.dm.allx[cp - self.dm.data_len: cp], \
                                   self.dm.appx_lo)


    def update_extreme_lo(self, cp):
        keep = 0
        if (len(self.dm.cur_appx_lo) == 0):
            self.dm.cur_appx_lo = self.dm.appx_lo
            self.dm.cur_appx_epos = cp
            self.dm.cur_appx_spos = self.dm.cur_appx_epos - self.dm.data_len
            self.dm.cur_ext_pos = self.dm.ext_pos
            self.dm.cur_ext_val = self.dm.ext_val
            keep = 2
        else:
            # get the differ
            keep = select_appx(self.dm.all_data[cp - self.dm.data_len: cp],
                               self.dm.cur_appx_lo, self.dm.appx_lo,
                               self.dm.cur_ext_pos, self.dm.ext_pos,
                               self.dm.cur_appx_spos, self.dm.cur_appx_epos,
                               cp - self.dm.data_len, cp)
        if (keep == 2):
            self.dm.cur_appx_lo = self.dm.appx_lo
            self.dm.cur_appx_epos = cp
            self.dm.cur_appx_spos = self.dm.cur_appx_epos - self.dm.data_len
            self.dm.cur_ext_pos = self.dm.ext_pos
            self.dm.cur_ext_val = self.dm.ext_val
            self.lappx_hi.set_data(self.dm.allx[cp - self.dm.data_len: cp], \
                                   self.dm.appx_hi)
            self.lp_hi.set_data(self.dm.allx[cp: cp + self.dm.predict_len], \
                                self.dm.ap_hi)
            self.lExtrem.set_data(self.dm.cur_ext_pos, self.dm.cur_ext_val)



    def update_extreme_mid(self, cp):
        keep = 0
        if (len(self.dm.cur_appx_mid) == 0):
            self.dm.cur_appx_mid = self.dm.appx_mid
            self.dm.cur_ext_mid_pos = self.dm.ext_mid_pos
            self.dm.cur_ext_mid_val = self.dm.ext_mid_val
            keep = 2
        else:
            # get the differ
            keep = select_appx(self.dm.all_data[cp - self.dm.data_len: cp],\
                               self.dm.cur_appx_mid, self.dm.appx_mid,\
                               self.dm.cur_ext_mid_pos, self.dm.ext_mid_pos,\
                               self.dm.cur_appx_spos, self.dm.cur_appx_epos,\
                               cp - self.dm.data_len, cp)
        if (keep == 2):
            self.dm.cur_appx_mid = self.dm.appx_mid
            self.dm.cur_ext_mid_pos = self.dm.ext_mid_pos
            self.dm.cur_ext_mid_val = self.dm.ext_mid_val
            self.lappx_mid.set_data(self.dm.allx[cp - self.dm.data_len: cp], \
                                   self.dm.appx_mid)
            self.lExtremMid.set_data(self.dm.cur_ext_mid_pos, self.dm.cur_ext_mid_val)


    def update_revenue(self, xlim, ylim, cur_pos):
        if (self.name == 'art2'):
            return

        rev = 0

        self.txtTrade.set_position((xlim[1] - 100, ylim[1] - 3))
        if (1 == len(self.trade.order) % 2):
            if self.trade.order[-1].direct == 'a':
                rev = (self.dm.all_data[cur_pos] - self.trade.order[-1].price) * 10
                self.txtTrade.set_color('red')
                self.txtTrade.set_text('Long')
            else:
                rev = (self.trade.order[-1].price - self.dm.all_data[cur_pos]) * 10
                self.txtTrade.set_color('green')
                self.txtTrade.set_text('Short')
        else:
            self.txtTrade.set_text('')

        self.txtRev.set_position((xlim[1] - 100, ylim[1] - 8))
        if rev == 0:
            str_rev = ''
        else:
            str_rev = str(rev)

        if (rev > 0):
            self.txtRev.set_color('red')
        else:
            self.txtRev.set_color('green')
        self.txtRev.set_text(str_rev)

        self.txtAllRev.set_position((xlim[1] - 100, ylim[1] - 13))
        if (self.trade.allrev == 0):
            str_all_rev = ''
        else:
            str_all_rev = str(self.trade.allrev)
        if (self.trade.allrev > 0):
            self.txtAllRev.set_color('red')
        else:
            self.txtAllRev.set_color('green')
        self.txtAllRev.set_text(str_all_rev)


    def animate(self, cur_pos, pass_pos, its_review, show_future):
        # print self.name, " : ", cur_pos

        cp = cur_pos / self.down_int
        pp = pass_pos / self.down_int

        if (cp + self.dm.predict_len > self.dm.all_len):
            return

        xlim = list(self.ax.get_xlim())
        ylim = list(self.ax.get_ylim())

        self.update_limite(xlim, ylim, cp)

        self.dm.do_math(cp)

        self.update_lines(xlim, cp, pp, its_review, show_future)
        self.update_revenue(xlim, ylim, cp)

        '''
        TODO: Add your trade algorithm HERE!
        '''

        return tuple(self.lines) + (self.txtTrade, self.txtRev, self.txtAllRev)





class SubplotAnimation(animation.TimedAnimation):
    def __init__(self, dm1, dm2):
        self.fig = plt.figure()
        self.ax1 = self.fig.add_subplot(2, 1, 1)
        self.ax2 = self.fig.add_subplot(2, 1, 2)
        self.dm1 = dm1
        self.dm2 = dm2

        self.trade = Trade(dm1)

        self.art1 = Artist(dm1, self.ax1, "art1")
        self.art1.set_trade(self.trade)

        self.art2 = Artist(dm2, self.ax2, "art2")
        self.art2.set_dm_int(dm2.down_int)

        self.anim_running = True
        self.anim_interval = 200

        self.cur_pos = dm1.data_len
        self.max_curpos = self.cur_pos
        self.pass_pos = 0
        self.show_future = False
        self.its_review = False

        self.fig.canvas.mpl_connect('key_press_event', self.press)
        self.fig.canvas.mpl_connect('close_event', self.handle_close)
        # self.fig.canvas.mpl_connect('button_press_event', self.onClick)
        self.event_source = self.fig.canvas.new_timer()
        self.event_source.interval = self.anim_interval


        animation.TimedAnimation.__init__(self, self.fig, interval=self.anim_interval,
                                          event_source=self.event_source,blit=True)


    # def onClick(self, event):
    #    # print(event.button, event.xdata, event.ydata)
    #    # if (event.button == 3):
    #    self.show_future = not self.show_future


    def handle_close(self, evt):
        if self.dm1.closePosition(self.cur_pos):
            self.art1.strTrade = ''
            self.art1.strAllRev = str(self.dm1.allrev)
        self.event_source.stop()


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

        self._drawn_artists = self.art1.animate(self.cur_pos, self.pass_pos, self.its_review, self.show_future)\
                              + self.art2.animate(self.cur_pos, self.pass_pos, self.its_review, self.show_future)

        self.max_curpos = max(self.cur_pos, self.max_curpos)

        self.pass_pos = self.cur_pos - dm1.data_len

        if self.cur_pos < dm1.all_len - dm1.predict_len:
            self.cur_pos += 1


    def new_frame_seq(self):
        return iter(range(dm1.all_len))


    def _init_draw(self):
        self.cur_pos = 1024 * 10
        self.art1.init_animation()
        self.art2.init_animation()

if __name__ == "__main__":
    if (len(sys.argv) != 3):
        print 'Usage: python rb-subplot-game.py <r|the trade day> <data file path>\n'\
              '       1. r means you want a random day\n'\
              '          format of trade day is YYYYMMDD\n'\
              '       2. the data file path tell game where is the store of history data\n'\
              '       For example:\n' \
              '         get random trade-day data\n'\
              '           python rb-subplot-game.py r /data/sean/20170508/bindata/rb888\n'\
              '         get one day data\n'\
              '           python rb-subplot-game.py 20150601 /data/sean/20170508/bindata/rb888'
        '''
        Keyboard:
            i:	pause/continue
            a: 	open long
            b:	open short
            c: 	close current position
            h: 	go back 10 datas
            l:	go forward 10 datas
            e:  show error in console
            t:  toggle disable/enable future data
            =:  accelatate the paly speed
            -:	make the play speed slow down
        '''
    else:
    # all_data, all_ask, all_bid, all_len, allx, the_date = get_data()
        ret, all_data, all_ask, all_bid, all_len, allx, the_date = get_data_from_file(sys.argv)
        if (ret == 0):
            dm1 = DataMath(all_data, all_ask, all_bid, all_len, allx, the_date)
            dm2 = DataMath(all_data, all_ask, all_bid, all_len, allx, the_date)
            dm2.down_sample(20)
            opq = str(raw_input("enter something to draw: "))
            params = {'legend.fontsize': 'small',
                      'figure.figsize': (48, 21),
                      'axes.labelsize': 'small',
                      'axes.titlesize':'small',
                      'xtick.labelsize':'small',
                      'ytick.labelsize':'small'}

            ani = SubplotAnimation(dm1, dm2)
            # ani.save('test_sub.mp4')
            plt.show()
