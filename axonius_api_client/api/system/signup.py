# -*- coding: utf-8 -*-
"""API for performing initial signup."""
from ...constants.logs import LOG_LEVEL_API
from ...exceptions import ResponseNotOk
from ...http import Http
from ...logs import get_obj_log
from ..routers import API_VERSION, Router


class Signup:
    """API for performing initial signup.

    Examples:
        * Check if initial signup has been done: :meth:`is_signed_up`
        * Perform initial signup: :meth:`signup`

    """

    @property
    def is_signed_up(self) -> bool:
        """Check if initial signup has been done.

        Examples:
            >>> signup = axonius_api_client.Signup(url="10.20.0.61")
            >>> signup.is_signed_up
            True
        """
        return self._signup_get()["signup"]

    def signup(self, password: str, company_name: str, contact_email: str) -> dict:
        """Perform the initial signup and get the API key and API secret of admin user.

        Examples:
            >>> signup = axonius_api_client.Signup(url="10.20.0.61")
            >>> data = signup.signup(
            ...     password="demo", company_name="Axonius", contact_email="jim@axonius.com"
            ... )
            >>> data
            {'api_key': 'xxxx', 'api_secret': 'xxxx'}

        Args:
            password: password for admin user
            company_name: name of company
            contact_email: email address of company contact
        """
        response = self._signup_post(
            password=password, company_name=company_name, contact_email=contact_email
        )

        status = response.get("status")
        message = response.get("message")
        if status == "error":
            raise ResponseNotOk(f"{message}")
        return response  # pragma: no cover

    def _signup_get(self) -> dict:
        """Get the status of initial signup."""
        response = self.http(method="get", path=self.router.root)
        return response.json()

    def _signup_post(self, password: str, company_name: str, contact_email: str) -> dict:
        """Do the initial signup."""
        data = {
            "companyName": company_name,
            "contactEmail": contact_email,
            "userName": "admin",
            "newPassword": password,
            "confirmNewPassword": password,
            "api_keys": True,
        }
        response = self.http(method="post", path=self.router.root, json=data)
        return response.json()

    @property
    def router(self) -> Router:
        """Router for this API model."""
        return API_VERSION.signup

    def __init__(self, url, **kwargs):
        """Provide an API for performing initial signup.

        Args:
            url: url of instance to perform signup against
            **kwargs: passed thru to :obj:`axonius_api_client.http.Http`
        """
        log_level = kwargs.get("log_level", LOG_LEVEL_API)
        self.LOG = get_obj_log(obj=self, level=log_level)
        kwargs.setdefault("certwarn", False)
        self.http = Http(url=url, **kwargs)
