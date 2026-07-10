"""
Tests for the legacy format_helpers module.
Tests the old-style formatting functions including warranty label formatting.
"""

import datetime
import pytest

from app.legacy.format_helpers import (
    format_warranty_label,
    summarize_status_counts,
)


class TestFormatWarrantyLabel:
    """Test warranty label formatting with various expiry scenarios."""

    def test_expired_warranty_far_past(self):
        """Test formatting for warranty expired long ago."""
        asset_tag = "TEST-001"
        expiry_date = datetime.date.today() - datetime.timedelta(days=100)
        
        result = format_warranty_label(asset_tag, expiry_date)
        
        assert "TEST-001" in result
        assert "EXPIRED" in result
        assert "100 days ago" in result

    def test_expired_warranty_recently(self):
        """Test formatting for recently expired warranty."""
        asset_tag = "TEST-002"
        expiry_date = datetime.date.today() - datetime.timedelta(days=5)
        
        result = format_warranty_label(asset_tag, expiry_date)
        
        assert "TEST-002" in result
        assert "EXPIRED" in result
        assert "5 days ago" in result

    def test_expiring_within_30_days_urgent(self):
        """Test formatting for warranty expiring within 30 days (urgent)."""
        asset_tag = "TEST-003"
        expiry_date = datetime.date.today() + datetime.timedelta(days=15)
        
        result = format_warranty_label(asset_tag, expiry_date)
        
        assert "TEST-003" in result
        assert "expires in 15 days" in result
        assert "URGENT" in result

    def test_expiring_exactly_29_days_urgent(self):
        """Test formatting for warranty expiring in exactly 29 days."""
        asset_tag = "TEST-004"
        expiry_date = datetime.date.today() + datetime.timedelta(days=29)
        
        result = format_warranty_label(asset_tag, expiry_date)
        
        assert "TEST-004" in result
        assert "expires in 29 days" in result
        assert "URGENT" in result

    def test_expiring_30_days_or_more(self):
        """Test formatting for warranty expiring 30 or more days out."""
        asset_tag = "TEST-005"
        expiry_date = datetime.date.today() + datetime.timedelta(days=90)
        
        result = format_warranty_label(asset_tag, expiry_date)
        
        assert "TEST-005" in result
        assert "expires" in result
        assert "URGENT" not in result
        assert expiry_date.strftime("%Y-%m-%d") in result

    def test_expiring_exactly_30_days(self):
        """Test formatting for warranty expiring in exactly 30 days."""
        asset_tag = "TEST-006"
        expiry_date = datetime.date.today() + datetime.timedelta(days=30)
        
        result = format_warranty_label(asset_tag, expiry_date)
        
        assert "TEST-006" in result
        assert "expires" in result
        # Should not be marked urgent at exactly 30 days
        assert "URGENT" not in result

    def test_expiring_far_future(self):
        """Test formatting for warranty expiring far in the future."""
        asset_tag = "TEST-007"
        expiry_date = datetime.date.today() + datetime.timedelta(days=365)
        
        result = format_warranty_label(asset_tag, expiry_date)
        
        assert "TEST-007" in result
        assert "expires" in result
        assert "URGENT" not in result

    def test_expiring_today(self):
        """Test formatting for warranty expiring today."""
        asset_tag = "TEST-008"
        expiry_date = datetime.date.today()
        
        result = format_warranty_label(asset_tag, expiry_date)
        
        assert "TEST-008" in result
        assert "expires in 0 days" in result
        assert "URGENT" in result


class TestSummarizeStatusCounts:
    """Test status count summarization."""

    def test_empty_counts(self):
        """Test with empty dictionary."""
        result = summarize_status_counts({})
        assert result == ""

    def test_single_status(self):
        """Test with single status."""
        result = summarize_status_counts({"available": 5})
        assert "available=5" in result

    def test_multiple_statuses(self):
        """Test with multiple statuses."""
        result = summarize_status_counts({
            "available": 10,
            "assigned": 7,
            "retired": 3
        })
        
        assert "available=10" in result
        assert "assigned=7" in result
        assert "retired=3" in result

    def test_zero_counts(self):
        """Test with zero counts."""
        result = summarize_status_counts({
            "available": 0,
            "assigned": 0
        })
        
        assert "available=0" in result
        assert "assigned=0" in result
