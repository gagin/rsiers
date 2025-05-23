# scripts/manual_data_filler.py

import datetime as dt 
from datetime import timezone
import logging
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.db_utils import init_db as init_db_main, store_daily_ohlcv_data, DB_PATH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- DATA TO BE MANUALLY FILLED ---
# Data provided by user, assuming source is 'manual_fill_yahoo_finance_format'
# or similar.
data_to_fill = [
    {"date_str": "May 22, 2025", "open_str": "109,673.49", "high_str": "111,970.17", "low_str": "109,285.07", "close_str": "111,673.28", "volume_str": "70,157,575,642", "source": "manual_fill_yahoo_format"},
    {"date_str": "May 21, 2025", "open_str": "106,791.31", "high_str": "110,724.46", "low_str": "106,127.23", "close_str": "109,678.08", "volume_str": "78,086,364,051", "source": "manual_fill_yahoo_format"},
    {"date_str": "May 20, 2025", "open_str": "105,605.41", "high_str": "107,307.12", "low_str": "104,206.52", "close_str": "106,791.09", "volume_str": "36,515,726,122", "source": "manual_fill_yahoo_format"},
    {"date_str": "May 19, 2025", "open_str": "106,430.53", "high_str": "107,068.72", "low_str": "102,112.69", "close_str": "105,606.18", "volume_str": "61,761,126,647", "source": "manual_fill_yahoo_format"},
    {"date_str": "May 18, 2025", "open_str": "103,186.95", "high_str": "106,597.17", "low_str": "103,142.60", "close_str": "106,446.01", "volume_str": "49,887,082,058", "source": "manual_fill_yahoo_format"},
    {"date_str": "May 17, 2025", "open_str": "103,489.29", "high_str": "103,716.95", "low_str": "102,659.18", "close_str": "103,191.09", "volume_str": "37,898,552,742", "source": "manual_fill_yahoo_format"},
    {"date_str": "May 16, 2025", "open_str": "103,735.66", "high_str": "104,533.48", "low_str": "103,137.48", "close_str": "103,489.29", "volume_str": "44,386,499,364", "source": "manual_fill_yahoo_format"},
    {"date_str": "May 15, 2025", "open_str": "103,538.83", "high_str": "104,153.62", "low_str": "101,440.81", "close_str": "103,744.64", "volume_str": "50,408,241,840", "source": "manual_fill_yahoo_format"},
    {"date_str": "May 14, 2025", "open_str": "104,167.33", "high_str": "104,303.56", "low_str": "102,618.30", "close_str": "103,539.41", "volume_str": "45,956,071,155", "source": "manual_fill_yahoo_format"},
    {"date_str": "May 13, 2025", "open_str": "102,812.49", "high_str": "104,997.42", "low_str": "101,515.09", "close_str": "104,169.81", "volume_str": "52,608,876,410", "source": "manual_fill_yahoo_format"},
    {"date_str": "May 12, 2025", "open_str": "104,106.96", "high_str": "105,747.45", "low_str": "100,814.41", "close_str": "102,812.95", "volume_str": "63,250,475,404", "source": "manual_fill_yahoo_format"},
    {"date_str": "May 11, 2025", "open_str": "104,701.07", "high_str": "104,937.99", "low_str": "103,364.74", "close_str": "104,106.36", "volume_str": "46,285,517,406", "source": "manual_fill_yahoo_format"},
    {"date_str": "May 10, 2025", "open_str": "102,973.71", "high_str": "104,961.77", "low_str": "102,830.48", "close_str": "104,696.33", "volume_str": "42,276,713,994", "source": "manual_fill_yahoo_format"},
    {"date_str": "May 9, 2025", "open_str": "103,239.13", "high_str": "104,297.49", "low_str": "102,343.09", "close_str": "102,970.85", "volume_str": "58,198,593,958", "source": "manual_fill_yahoo_format"},
    {"date_str": "May 8, 2025", "open_str": "97,034.25", "high_str": "103,969.54", "low_str": "96,913.88", "close_str": "103,241.46", "volume_str": "69,895,404,397", "source": "manual_fill_yahoo_format"},
    {"date_str": "May 7, 2025", "open_str": "96,800.20", "high_str": "97,625.80", "low_str": "95,829.34", "close_str": "97,032.32", "volume_str": "76,983,822,462", "source": "manual_fill_yahoo_format"},
    {"date_str": "May 6, 2025", "open_str": "94,748.38", "high_str": "96,889.18", "low_str": "93,399.86", "close_str": "96,802.48", "volume_str": "26,551,275,827", "source": "manual_fill_yahoo_format"},
    {"date_str": "May 5, 2025", "open_str": "94,319.56", "high_str": "95,193.19", "low_str": "93,566.27", "close_str": "94,748.05", "volume_str": "25,816,260,327", "source": "manual_fill_yahoo_format"},
    {"date_str": "May 4, 2025", "open_str": "95,877.19", "high_str": "96,318.92", "low_str": "94,173.43", "close_str": "94,315.98", "volume_str": "18,198,688,416", "source": "manual_fill_yahoo_format"},
    {"date_str": "May 3, 2025", "open_str": "96,904.63", "high_str": "96,943.88", "low_str": "95,821.29", "close_str": "95,891.80", "volume_str": "15,775,154,889", "source": "manual_fill_yahoo_format"},
    {"date_str": "May 2, 2025", "open_str": "96,494.97", "high_str": "97,905.90", "low_str": "96,375.95", "close_str": "96,910.07", "volume_str": "26,421,924,677", "source": "manual_fill_yahoo_format"},
    {"date_str": "May 1, 2025", "open_str": "94,212.86", "high_str": "97,437.96", "low_str": "94,153.63", "close_str": "96,492.34", "volume_str": "32,875,889,623", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 30, 2025", "open_str": "94,286.47", "high_str": "95,249.32", "low_str": "92,979.64", "close_str": "94,207.31", "volume_str": "28,344,679,831", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 29, 2025", "open_str": "94,981.86", "high_str": "95,485.41", "low_str": "93,796.63", "close_str": "94,284.79", "volume_str": "25,806,129,921", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 28, 2025", "open_str": "93,755.30", "high_str": "95,598.49", "low_str": "92,860.80", "close_str": "94,978.75", "volume_str": "32,363,449,569", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 27, 2025", "open_str": "94,660.91", "high_str": "95,301.20", "low_str": "93,665.40", "close_str": "93,754.84", "volume_str": "18,090,367,764", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 26, 2025", "open_str": "94,714.65", "high_str": "95,251.36", "low_str": "93,927.25", "close_str": "94,646.93", "volume_str": "17,612,825,123", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 25, 2025", "open_str": "93,954.25", "high_str": "95,768.39", "low_str": "92,898.59", "close_str": "94,720.50", "volume_str": "40,915,232,364", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 24, 2025", "open_str": "93,692.40", "high_str": "94,016.20", "low_str": "91,696.71", "close_str": "93,943.80", "volume_str": "31,483,175,315", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 23, 2025", "open_str": "93,427.59", "high_str": "94,535.73", "low_str": "91,962.96", "close_str": "93,699.11", "volume_str": "41,719,568,821", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 22, 2025", "open_str": "87,521.88", "high_str": "93,817.38", "low_str": "87,084.53", "close_str": "93,441.89", "volume_str": "55,899,038,456", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 21, 2025", "open_str": "85,171.54", "high_str": "88,460.09", "low_str": "85,143.84", "close_str": "87,518.91", "volume_str": "41,396,190,190", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 20, 2025", "open_str": "85,066.07", "high_str": "85,306.38", "low_str": "83,976.84", "close_str": "85,174.30", "volume_str": "14,664,050,812", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 19, 2025", "open_str": "84,450.87", "high_str": "85,597.70", "low_str": "84,353.46", "close_str": "85,063.41", "volume_str": "15,259,300,427", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 18, 2025", "open_str": "84,900.19", "high_str": "85,095.05", "low_str": "84,298.88", "close_str": "84,450.80", "volume_str": "12,728,372,364", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 17, 2025", "open_str": "84,030.67", "high_str": "85,449.07", "low_str": "83,749.75", "close_str": "84,895.75", "volume_str": "21,276,866,029", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 16, 2025", "open_str": "83,674.51", "high_str": "85,428.28", "low_str": "83,100.62", "close_str": "84,033.87", "volume_str": "29,617,804,112", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 15, 2025", "open_str": "84,539.70", "high_str": "86,429.35", "low_str": "83,598.82", "close_str": "83,668.99", "volume_str": "28,040,322,885", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 14, 2025", "open_str": "83,694.52", "high_str": "85,785.00", "low_str": "83,690.64", "close_str": "84,542.39", "volume_str": "34,090,769,777", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 13, 2025", "open_str": "85,279.47", "high_str": "86,015.19", "low_str": "83,027.01", "close_str": "83,684.98", "volume_str": "28,796,984,817", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 12, 2025", "open_str": "83,404.52", "high_str": "85,856.19", "low_str": "82,769.38", "close_str": "85,287.11", "volume_str": "24,258,059,104", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 11, 2025", "open_str": "79,625.05", "high_str": "84,247.48", "low_str": "78,936.32", "close_str": "83,404.84", "volume_str": "41,656,778,779", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 10, 2025", "open_str": "82,565.98", "high_str": "82,700.93", "low_str": "78,456.13", "close_str": "79,626.14", "volume_str": "44,718,000,633", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 9, 2025", "open_str": "76,273.56", "high_str": "83,541.00", "low_str": "74,589.67", "close_str": "82,573.95", "volume_str": "84,213,627,038", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 8, 2025", "open_str": "79,218.48", "high_str": "80,823.89", "low_str": "76,198.02", "close_str": "76,271.95", "volume_str": "48,314,590,749", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 7, 2025", "open_str": "78,221.34", "high_str": "81,119.06", "low_str": "74,436.68", "close_str": "79,235.34", "volume_str": "91,262,424,987", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 6, 2025", "open_str": "83,504.51", "high_str": "83,704.72", "low_str": "77,097.74", "close_str": "78,214.48", "volume_str": "36,294,853,736", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 5, 2025", "open_str": "83,844.70", "high_str": "84,207.02", "low_str": "82,377.73", "close_str": "83,504.80", "volume_str": "14,380,803,631", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 4, 2025", "open_str": "83,100.25", "high_str": "84,696.15", "low_str": "81,670.75", "close_str": "83,843.80", "volume_str": "45,157,640,207", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 3, 2025", "open_str": "82,487.48", "high_str": "83,909.30", "low_str": "81,282.10", "close_str": "83,102.83", "volume_str": "36,852,112,080", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 2, 2025", "open_str": "85,180.61", "high_str": "88,466.95", "low_str": "82,343.54", "close_str": "82,485.71", "volume_str": "47,584,398,470", "source": "manual_fill_yahoo_format"},
    {"date_str": "Apr 1, 2025", "open_str": "82,551.92", "high_str": "85,487.37", "low_str": "82,429.36", "close_str": "85,169.17", "volume_str": "28,175,650,319", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 31, 2025", "open_str": "82,336.06", "high_str": "83,870.13", "low_str": "81,293.89", "close_str": "82,548.91", "volume_str": "29,004,228,247", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 30, 2025", "open_str": "82,596.98", "high_str": "83,505.00", "low_str": "81,573.25", "close_str": "82,334.52", "volume_str": "14,763,760,943", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 29, 2025", "open_str": "84,352.07", "high_str": "84,567.34", "low_str": "81,634.14", "close_str": "82,597.59", "volume_str": "16,969,396,135", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 28, 2025", "open_str": "87,185.23", "high_str": "87,489.86", "low_str": "83,557.64", "close_str": "84,353.15", "volume_str": "34,198,619,509", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 27, 2025", "open_str": "86,896.26", "high_str": "87,786.73", "low_str": "85,837.94", "close_str": "87,177.10", "volume_str": "24,413,471,941", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 26, 2025", "open_str": "87,460.23", "high_str": "88,292.16", "low_str": "85,861.45", "close_str": "86,900.88", "volume_str": "26,704,046,038", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 25, 2025", "open_str": "87,512.82", "high_str": "88,542.40", "low_str": "86,346.08", "close_str": "87,471.70", "volume_str": "30,005,840,049", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 24, 2025", "open_str": "86,070.93", "high_str": "88,758.73", "low_str": "85,541.20", "close_str": "87,498.91", "volume_str": "34,582,604,933", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 23, 2025", "open_str": "83,831.90", "high_str": "86,094.78", "low_str": "83,794.91", "close_str": "86,054.38", "volume_str": "12,594,615,537", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 22, 2025", "open_str": "84,046.26", "high_str": "84,513.88", "low_str": "83,674.78", "close_str": "83,832.48", "volume_str": "9,863,214,091", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 21, 2025", "open_str": "84,164.54", "high_str": "84,782.27", "low_str": "83,171.07", "close_str": "84,043.24", "volume_str": "19,030,452,299", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 20, 2025", "open_str": "86,872.95", "high_str": "87,443.27", "low_str": "83,647.20", "close_str": "84,167.20", "volume_str": "29,028,988,961", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 19, 2025", "open_str": "82,718.80", "high_str": "87,021.19", "low_str": "82,569.73", "close_str": "86,854.23", "volume_str": "34,931,960,257", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 18, 2025", "open_str": "84,075.72", "high_str": "84,075.72", "low_str": "81,179.99", "close_str": "82,718.50", "volume_str": "24,095,774,594", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 17, 2025", "open_str": "82,576.34", "high_str": "84,725.33", "low_str": "82,492.16", "close_str": "84,075.69", "volume_str": "25,092,785,558", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 16, 2025", "open_str": "84,333.32", "high_str": "85,051.60", "low_str": "82,017.91", "close_str": "82,579.69", "volume_str": "21,330,270,174", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 15, 2025", "open_str": "83,968.41", "high_str": "84,672.67", "low_str": "83,639.59", "close_str": "84,343.11", "volume_str": "13,650,491,277", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 14, 2025", "open_str": "81,066.99", "high_str": "85,263.29", "low_str": "80,797.56", "close_str": "83,969.10", "volume_str": "29,588,112,414", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 13, 2025", "open_str": "83,724.92", "high_str": "84,301.70", "low_str": "79,931.85", "close_str": "81,066.70", "volume_str": "31,412,940,153", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 12, 2025", "open_str": "82,857.38", "high_str": "84,358.58", "low_str": "80,635.25", "close_str": "83,722.36", "volume_str": "40,353,484,454", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 11, 2025", "open_str": "78,523.88", "high_str": "83,577.76", "low_str": "76,624.25", "close_str": "82,862.21", "volume_str": "54,702,837,196", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 10, 2025", "open_str": "80,597.15", "high_str": "83,955.93", "low_str": "77,420.59", "close_str": "78,532.00", "volume_str": "54,061,099,422", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 9, 2025", "open_str": "86,154.30", "high_str": "86,471.13", "low_str": "80,052.48", "close_str": "80,601.04", "volume_str": "30,899,345,977", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 8, 2025", "open_str": "86,742.66", "high_str": "86,847.27", "low_str": "85,247.48", "close_str": "86,154.59", "volume_str": "18,206,118,081", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 7, 2025", "open_str": "89,963.28", "high_str": "91,191.05", "low_str": "84,717.68", "close_str": "86,742.67", "volume_str": "65,945,677,657", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 6, 2025", "open_str": "90,622.36", "high_str": "92,804.94", "low_str": "87,852.14", "close_str": "89,961.73", "volume_str": "47,749,810,486", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 5, 2025", "open_str": "87,222.95", "high_str": "90,998.24", "low_str": "86,379.77", "close_str": "90,623.56", "volume_str": "50,498,988,027", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 4, 2025", "open_str": "86,064.07", "high_str": "88,911.27", "low_str": "81,529.24", "close_str": "87,222.20", "volume_str": "68,095,241,474", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 3, 2025", "open_str": "94,248.42", "high_str": "94,429.75", "low_str": "85,081.30", "close_str": "86,065.67", "volume_str": "70,072,228,536", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 2, 2025", "open_str": "86,036.26", "high_str": "95,043.44", "low_str": "85,040.21", "close_str": "94,248.35", "volume_str": "58,398,341,092", "source": "manual_fill_yahoo_format"},
    {"date_str": "Mar 1, 2025", "open_str": "84,373.87", "high_str": "86,522.30", "low_str": "83,794.23", "close_str": "86,031.91", "volume_str": "29,190,628,396", "source": "manual_fill_yahoo_format"},
    {"date_str": "Feb 28, 2025", "open_str": "84,705.63", "high_str": "85,036.32", "low_str": "78,248.91", "close_str": "84,373.01", "volume_str": "83,610,570,576", "source": "manual_fill_yahoo_format"},
    {"date_str": "Feb 27, 2025", "open_str": "84,076.86", "high_str": "87,000.78", "low_str": "83,144.96", "close_str": "84,704.23", "volume_str": "52,659,591,954", "source": "manual_fill_yahoo_format"},
    {"date_str": "Feb 26, 2025", "open_str": "88,638.89", "high_str": "89,286.25", "low_str": "82,131.90", "close_str": "84,347.02", "volume_str": "64,597,492,134", "source": "manual_fill_yahoo_format"},
    {"date_str": "Feb 25, 2025", "open_str": "91,437.12", "high_str": "92,511.08", "low_str": "86,008.23", "close_str": "88,736.17", "volume_str": "92,139,104,128", "source": "manual_fill_yahoo_format"},
    {"date_str": "Feb 24, 2025", "open_str": "96,277.96", "high_str": "96,503.45", "low_str": "91,371.74", "close_str": "91,418.17", "volume_str": "44,046,480,529", "source": "manual_fill_yahoo_format"},
    {"date_str": "Feb 23, 2025", "open_str": "96,577.80", "high_str": "96,671.88", "low_str": "95,270.45", "close_str": "96,273.92", "volume_str": "16,999,478,976", "source": "manual_fill_yahoo_format"}
]

def parse_value(value_str: str) -> float:
    """Removes commas and converts to float."""
    return float(str(value_str).replace(',', ''))

def main():
    logger.info(f"Starting manual data fill script. DB: {DB_PATH}")
    init_db_main() 

    if not data_to_fill:
        logger.info("No data specified in the 'data_to_fill' list. Exiting.")
        return

    entries_processed = 0
    entries_failed = 0

    for entry in data_to_fill:
        try:
            date_obj_naive = dt.datetime.strptime(entry["date_str"], "%b %d, %Y")
            date_obj_utc_start_of_day = date_obj_naive.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)

            ohlcv_values = {
                'open': parse_value(entry["open_str"]),
                'high': parse_value(entry["high_str"]),
                'low': parse_value(entry["low_str"]),
                'close': parse_value(entry["close_str"]), # Using "Close", not "Adj Close"
                'volume': parse_value(entry["volume_str"]),
                'source': entry["source"],
            }
            
            logger.info(f"Attempting to store data for {entry['date_str']} (Normalized UTC date: {date_obj_utc_start_of_day.strftime('%Y-%m-%d')})")
            store_daily_ohlcv_data(date_obj_utc_start_of_day, ohlcv_values)
            entries_processed +=1

        except ValueError as ve:
            logger.error(f"Skipping entry due to ValueError parsing data for '{entry['date_str']}': {ve}")
            entries_failed +=1
        except Exception as e:
            logger.error(f"An unexpected error occurred processing entry for '{entry['date_str']}': {e}", exc_info=True)
            entries_failed +=1

    logger.info(f"Manual data fill script finished. Processed: {entries_processed}, Failed: {entries_failed}")

if __name__ == "__main__":
    main()