from logic.power_bands import PwrBands
from constants import BAND_POWERS
from utils import tanh_normalize

class NeuroFB(PwrBands):
    FOCUS = "Focus"
    RELAX = "Relax"
    SIGNED = ""
    UNSIGNED = "Pos"
    FOCUS_AVG_SIDE = "FocusAvgSide"

    def __init__(self, board, window_seconds=2, normalize_scale=1.1, ema_decay=0.025):
        super().__init__(board, window_seconds=window_seconds, ema_decay=ema_decay)
        self.normalize_scale = normalize_scale

    def get_data_dict(self):
        power_dict = super().get_data_dict()

        # create functions for getting scores per location
        get_focus = lambda location: self.calculate_ratio(
            power_dict[location][BAND_POWERS.Beta.name], 
            power_dict[location][BAND_POWERS.Theta.name])
        get_relax = lambda location: self.calculate_ratio(
            power_dict[location][BAND_POWERS.Alpha.name], 
            power_dict[location][BAND_POWERS.Theta.name])
        
        # create a function dict to apply calculations with
        # and return dict to aggregate values
        function_dict = {
            NeuroFB.FOCUS: get_focus,
            NeuroFB.RELAX: get_relax
        }
        ret_dict = {}

        # apply score calculations per location and add to ret_dict
        for nfb_name, nfb_func in function_dict.items():
            signed_dict = {location + NeuroFB.SIGNED : nfb_func(location) for location in power_dict}
            unsigned_dict = {location + NeuroFB.UNSIGNED : (value+1)/2 for location, value in signed_dict.items()}
            inner_flat_dict = signed_dict | unsigned_dict
            inner_flat_dict = {nfb_name + key : value for key, value in inner_flat_dict.items()}
            ret_dict |= inner_flat_dict

        # Calculate FocusAvgSide using FocusLeftPos and FocusRightPos
        focus_left_pos = ret_dict.get(NeuroFB.FOCUS + PwrBands.LEFT + NeuroFB.UNSIGNED, 0)
        focus_right_pos = ret_dict.get(NeuroFB.FOCUS + PwrBands.RIGHT + NeuroFB.UNSIGNED, 0)

        focus_avg_side = focus_right_pos - focus_left_pos
        ret_dict[NeuroFB.FOCUS_AVG_SIDE] = focus_avg_side

        return ret_dict

    def calculate_ratio(self, numerator, denominator):
        return tanh_normalize(numerator / denominator, self.normalize_scale, -1)
