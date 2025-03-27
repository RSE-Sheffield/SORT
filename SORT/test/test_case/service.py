"""
A unit testing class for testing SORT application services.
"""

from typing import Optional
import django.test
from home.services.base import BasePermissionService


class ServiceTestCase(django.test.TestCase):
    """
    A test case for testing an application service layer.
    """

    def setUp(self):
        self.service: Optional[BasePermissionService] = None
