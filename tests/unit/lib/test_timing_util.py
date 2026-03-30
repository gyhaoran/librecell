"""
Task 02: Test timing utility functions
"""
import pytest
import numpy as np

from lclib.characterization.util import (
    CalcMode,
    TripPoints,
    is_rising_edge,
    is_falling_edge,
    transition_time,
    get_slew_time,
    get_input_to_output_delay,
)


@pytest.mark.unit
class TestTimingEnums:
    """Test timing-related enums."""

    def test_calc_mode_values(self):
        """CalcMode enum has expected values."""
        assert CalcMode.WORST.value == 1
        assert CalcMode.TYPICAL.value == 2
        assert CalcMode.BEST.value == 3


@pytest.mark.unit
class TestTripPoints:
    """Test TripPoints namedtuple."""

    def test_trip_points_creation(self):
        """TripPoints can be created with all required fields."""
        tp = TripPoints(
            input_threshold_rise=0.5,
            input_threshold_fall=0.5,
            output_threshold_rise=0.5,
            output_threshold_fall=0.5,
            slew_lower_threshold_rise=0.2,
            slew_upper_threshold_rise=0.8,
            slew_lower_threshold_fall=0.2,
            slew_upper_threshold_fall=0.8
        )
        assert tp.input_threshold_rise == 0.5
        assert tp.slew_upper_threshold_rise == 0.8

    def test_trip_points_is_namedtuple(self):
        """TripPoints is a namedtuple."""
        tp = TripPoints(
            input_threshold_rise=0.5,
            input_threshold_fall=0.5,
            output_threshold_rise=0.5,
            output_threshold_fall=0.5,
            slew_lower_threshold_rise=0.2,
            slew_upper_threshold_rise=0.8,
            slew_lower_threshold_fall=0.2,
            slew_upper_threshold_fall=0.8
        )
        assert hasattr(tp, '_fields')
        assert 'input_threshold_rise' in tp._fields


@pytest.mark.unit
class TestEdgeDetection:
    """Test signal edge detection functions."""

    def test_is_rising_edge_rising_signal(self):
        """Rising signal detected correctly."""
        voltage = np.array([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
        assert is_rising_edge(voltage) == True

    def test_is_rising_edge_falling_signal(self):
        """Falling signal returns False."""
        voltage = np.array([1.0, 0.8, 0.6, 0.4, 0.2, 0.0])
        assert is_rising_edge(voltage) == False

    def test_is_falling_edge_falling_signal(self):
        """Falling signal detected correctly."""
        voltage = np.array([1.0, 0.8, 0.6, 0.4, 0.2, 0.0])
        assert is_falling_edge(voltage) == True

    def test_is_falling_edge_rising_signal(self):
        """Rising signal returns False."""
        voltage = np.array([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
        assert is_falling_edge(voltage) == False


@pytest.mark.unit
class TestTransitionTime:
    """Test transition time measurement."""

    def test_transition_time_rising_edge(self):
        """Measure transition time of rising edge."""
        time = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        voltage = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        t_cross = transition_time(voltage, time, threshold=0.5)
        assert t_cross is not None
        assert abs(t_cross - 2.0) < 0.01

    def test_transition_time_falling_edge(self):
        """Measure transition time of falling edge."""
        time = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        voltage = np.array([1.0, 0.75, 0.5, 0.25, 0.0])
        t_cross = transition_time(voltage, time, threshold=0.5)
        assert t_cross is not None
        assert abs(t_cross - 2.0) < 0.01

    def test_transition_time_no_crossing(self):
        """Return None when signal does not cross threshold."""
        time = np.array([0.0, 1.0, 2.0])
        voltage = np.array([0.1, 0.2, 0.3])
        t_cross = transition_time(voltage, time, threshold=0.5, n=0)
        assert t_cross is None


@pytest.mark.unit
class TestSlewTime:
    """Test slew time measurement."""

    def test_slew_time_rising_edge(self):
        """Measure slew time of rising edge."""
        time = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
        voltage = np.array([0.0, 0.0, 0.0, 0.0, 1.0, 1.0])

        trip_points = TripPoints(
            input_threshold_rise=0.5,
            input_threshold_fall=0.5,
            output_threshold_rise=0.5,
            output_threshold_fall=0.5,
            slew_lower_threshold_rise=0.2,
            slew_upper_threshold_rise=0.8,
            slew_lower_threshold_fall=0.2,
            slew_upper_threshold_fall=0.8
        )

        slew = get_slew_time(time, voltage, trip_points)
        assert slew >= 0

    def test_slew_time_falling_edge(self):
        """Measure slew time of falling edge."""
        time = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
        voltage = np.array([1.0, 1.0, 1.0, 1.0, 0.0, 0.0])

        trip_points = TripPoints(
            input_threshold_rise=0.5,
            input_threshold_fall=0.5,
            output_threshold_rise=0.5,
            output_threshold_fall=0.5,
            slew_lower_threshold_rise=0.2,
            slew_upper_threshold_rise=0.8,
            slew_lower_threshold_fall=0.2,
            slew_upper_threshold_fall=0.8
        )

        slew = get_slew_time(time, voltage, trip_points)
        assert slew >= 0


@pytest.mark.unit
class TestInputOutputDelay:
    """Test input-to-output delay measurement."""

    def test_delay_measurement(self):
        """Measure delay between input and output."""
        time = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        input_signal = np.array([0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0])
        output_signal = np.array([0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0])

        trip_points = TripPoints(
            input_threshold_rise=0.5,
            input_threshold_fall=0.5,
            output_threshold_rise=0.5,
            output_threshold_fall=0.5,
            slew_lower_threshold_rise=0.2,
            slew_upper_threshold_rise=0.8,
            slew_lower_threshold_fall=0.2,
            slew_upper_threshold_fall=0.8
        )

        delay = get_input_to_output_delay(time, input_signal, output_signal, trip_points)
        assert isinstance(delay, float)
        assert delay >= 0


@pytest.mark.unit
class TestDifferentialInputs:
    """Test differential input detection."""

    def test_find_differential_inputs_import(self):
        """find_differential_inputs_by_pattern can be imported."""
        from lclib.characterization.util import find_differential_inputs_by_pattern
        assert callable(find_differential_inputs_by_pattern)

    def test_differential_inputs_simple_pattern(self):
        """Find differential input pairs with simple pattern."""
        from lclib.characterization.util import find_differential_inputs_by_pattern

        patterns = ['INP,INN']
        input_pins = ['INP', 'INN', 'CLK']

        result = find_differential_inputs_by_pattern(patterns, input_pins)
        assert 'INP' in result
        assert result['INP'] == 'INN'
