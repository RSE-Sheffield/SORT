"""
A unit testing class for testing SORT application services.
"""

from typing import Optional

from home.services.base import BasePermissionService

from .base import SORTTestCase


class ServiceTestCase(SORTTestCase):
    """
    A test case for testing an application service layer.
    """

    def setUp(self):
        super().setUp()
        self.service: Optional[BasePermissionService] = None
