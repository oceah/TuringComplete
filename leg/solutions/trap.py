from typing import List

class Solution:
    def trap(self, height: List[int]) -> int:
        rain_water = 0
        left = 0
        right = len(height) - 1
        left_max = right_max = 0
        while left < right:
            if height[left] < height[right]:
                left_max = max(left_max, height[left])
                rain_water += left_max - height[left]
                left += 1
            else:
                right_max = max(right_max, height[right])
                rain_water += right_max - height[right]
                right -= 1
        return rain_water
