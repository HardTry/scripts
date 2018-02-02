import matplotlib.pyplot as plt

# rb-case-1 @2100592
# bpl = [-649.62, -649.48, -649.34, -649.20, -649.07, -648.95, -648.82, -648.70, -648.59, -648.48, -648.37, -648.27, -648.17, -648.08, -647.99, -647.90, -647.82, -647.74, -647.66, -647.59, -647.52, -647.46, -647.40, -647.35, -647.30, -647.25, -647.20, -647.17, -647.13, -647.10, -647.07, -647.05, -647.02, -647.01, -647.00, -646.99, -646.98, -646.98]
# hop = [-648.00, -650.00, -649.00, -651.00, -651.00, -649.00, -649.00, -650.00, -649.00, -651.00, -651.00, -649.00, -650.00, -649.00, -650.00, -649.00, -650.00, -648.00, -648.00, -649.00, -648.00, -651.00, -649.00, -647.00, -649.00, -646.00, -647.00, -654.00, -654.00, -651.00, -652.00, -649.00, -652.00, -649.00, -651.00, -650.00, -651.00, -648.00]
# apx = [-653.20, -653.03, -652.86, -652.69, -652.52, -652.36, -652.19, -652.03, -651.87, -651.71, -651.55, -651.40, -651.24, -651.09, -650.94, -650.79, -650.65, -650.50, -650.36, -650.22, -650.08, -649.95, -649.81, -649.68, -649.55, -649.42, -649.30, -649.17, -649.05, -648.93, -648.82, -648.70, -648.59, -648.48, -648.37, -648.27, -648.16, -648.06]

# rb-case-1 @2101984
# bpl = [-654.69, -654.42, -654.16, -653.90, -653.65, -653.41, -653.17, -652.95, -652.73, -652.52, -652.32, -652.13, -651.94, -651.77, -651.60, -651.44, -651.28, -651.14, -651.00, -650.87, -650.75, -650.64, -650.53, -650.43, -650.34, -650.26, -650.18, -650.11, -650.05, -649.99, -649.95, -649.91, -649.88, -649.85, -649.84, -649.83, -649.83]
# hop = [-647.00, -648.00, -652.00, -653.00, -648.00, -649.00, -652.00, -650.00, -652.00, -651.00, -655.00, -654.00, -650.00, -652.00, -649.00, -649.00, -651.00, -651.00, -646.00, -646.00, -650.00, -649.00, -654.00, -652.00, -650.00, -649.00, -651.00, -650.00, -647.00, -645.00, -648.00, -644.00, -652.00, -649.00, -654.00, -652.00, -656.00]
# apx = [-658.25, -657.93, -657.62, -657.31, -657.00, -656.70, -656.40, -656.10, -655.80, -655.50, -655.21, -654.92, -654.63, -654.35, -654.06, -653.78, -653.51, -653.23, -652.96, -652.70, -652.43, -652.17, -651.92, -651.67, -651.42, -651.17, -650.93, -650.70, -650.46, -650.24, -650.01, -649.79, -649.58, -649.37, -649.16, -648.96, -648.76]]
# attack! attack! 2104512, 6, 2104512 ~ 2104575
bpl = [-645.77, -645.47, -645.18, -644.90, -644.62, -644.35, -644.09, -643.83, -643.58, -643.33, -643.09, -642.86, -642.63, -642.41, -642.20, -641.99, -641.79, -641.59, -641.40, -641.22, -641.04, -640.87, -640.70, -640.54, -640.39, -640.24, -640.10, -639.96, -639.83, -639.71, -639.59, -639.48, -639.37, -639.27, -639.18, -639.09, -639.01, -638.93, -638.86, -638.79, -638.73, -638.67, -638.62, -638.57, -638.53, -638.49, -638.46, -638.43, -638.41, -638.40, -638.39, -638.38, -638.38]
hop = [-634.00, -637.00, -642.00, -639.00, -635.00, -632.00, -640.00, -637.00, -644.00, -641.00, -634.00, -635.00, -638.00, -638.00, -635.00, -636.00, -640.00, -641.00, -637.00, -638.00, -636.00, -638.00, -642.00, -644.00, -640.00, -639.00, -643.00, -641.00, -645.00, -641.00, -650.00, -646.00, -656.00, -650.00, -662.00, -660.00, -651.00, -653.00, -648.00, -651.00, -644.00, -645.00, -628.00, -630.00, -636.00, -634.00, -625.00, -629.00, -610.00, -609.00, -619.00, -619.00, -612.00]
apx = [-651.19, -650.75, -650.31, -649.87, -649.43, -648.99, -648.56, -648.12, -647.69, -647.26, -646.84, -646.41, -645.99, -645.57, -645.16, -644.75, -644.34, -643.93, -643.53, -643.13, -642.73, -642.33, -641.94, -641.55, -641.16, -640.78, -640.40, -640.02, -639.65, -639.28, -638.91, -638.55, -638.19, -637.83, -637.48, -637.13, -636.79, -636.45, -636.11, -635.78, -635.46, -635.14, -634.82, -634.51, -634.20, -633.90, -633.60, -633.31, -633.03, -632.75, -632.47, -632.21, -631.94]

x = list(range(len(bpl)))
plt.plot(x, bpl)
plt.plot(x, hop)
plt.plot(x, apx)

plt.show()