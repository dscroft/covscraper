import re
import sys
from urllib import parse

from bs4 import BeautifulSoup
from requests import Response, Session
from requests_ntlm import HttpNtlmAuth
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

disable_warnings(InsecureRequestWarning)


class AuthenticationFailure(Exception):
    def __init__(self, message):
        self.message = message


class Authenticator(Session):
    def __fail_condition(self, res: Response):
        return res.status_code in (400, 401, 403) or res.url in self.redirectPages

    def __auth_sonic(self):
        # login_url = "https://webapp.coventry.ac.uk/Sonic"
        self.auth = HttpNtlmAuth("COVENTRY\\{}".format(self.username), self.password)

    def __auth_kuali(self):
        kuali_url = "https://coventry.kuali.co/auth?return_to=https%3A%2F%2Fcoventry.kuali.co%2Fapps%2F"
        shibboleth_url = "https://idp2.coventry.ac.uk/idp/Authn/UserPassword"

        # shibboleth wont let us connect unless it looks like we've been redirected from an approved site
        res = Session.get(self, kuali_url)
        if res.status_code != 200:
            raise AuthenticationFailure(
                "Failed to load Kuali, HTTP {}".format(res.status_code)
            )

        # post the auth data to shibboleth
        data = {"j_username": self.username, "j_password": self.password}
        res = Session.post(self, shibboleth_url, data=data)
        if res.status_code != 200:
            raise AuthenticationFailure(
                "Failed to load shibboleth, HTTP {}".format(res.status_code)
            )

        # extract the auth key and post it
        soup = BeautifulSoup(res.text, "lxml")
        saml_url = soup.find("form", {"method": "post"})["action"]
        key = soup.find("input", {"name": "SAMLResponse"})["value"]
        res = Session.post(self, saml_url, data={"SAMLResponse": key})
        if res.status_code != 200:
            raise AuthenticationFailure(
                "Failed to post auth code, HTTP {}".format(res.status_code)
            )

    def __auth_aula(self):
        # It should be possible to have the system just login once and then cache the aula token to disk since it literally never expires.
        login_url = "https://api.coventry.aula.education/sso/login?redirect=https://coventry.aula.education/&email={}"
        if not self.username.endswith("coventry.ac.uk"):
            email = self.username + "@coventry.ac.uk"
        elif self.username.endswith("uni.coventry.ac.uk"):
            email = self.username.replace("@uni.", "@")
        else:
            email = self.username

        res = Session.get(self, login_url.format(email))
        if not res.status_code == 200:
            raise AuthenticationFailure(
                "Unable to begin SAML authentication chain with Aula, HTTP {}".format(
                    res.status_code
                )
            )

        soup = BeautifulSoup(res.text, "lxml")
        saml_url = soup.find("form", {"method": "post", "id": "options"})["action"]
        method = soup.find("input", {"name": "AuthMethod"})["value"]
        data = {"UserName": email, "Password": self.password, "AuthMethod": method}
        res = Session.post(self, saml_url, data=data)
        if res.status_code != 200:
            raise AuthenticationFailure(
                "Failed to post auth code Stage 1, HTTP {}".format(res.status_code)
            )
        soup = BeautifulSoup(res.text, "lxml")
        saml_url = soup.find("form", {"method": "POST"})["action"]
        key = soup.find("input", {"name": "SAMLResponse"})["value"]
        state = soup.find("input", {"name": "RelayState"})["value"]
        data = {"SAMLResponse": key, "RelayState": state}
        res = Session.post(
            self,
            saml_url,
            data=data,
            headers={"Referer": "https://federatedauth.coventry.ac.uk/"},
        )
        if res.status_code != 200:
            raise AuthenticationFailure(
                "Failed to post auth code Stage 2, HTTP {}".format(res.status_code)
            )
        soup = BeautifulSoup(res.text, "lxml")
        saml_url = soup.find("form", {"method": "post"})["action"]
        key = soup.find("input", {"name": "SAMLResponse"})["value"]
        state = soup.find("input", {"name": "RelayState"})["value"]
        data = {"SAMLResponse": key, "RelayState": state}
        res = Session.post(
            self,
            saml_url,
            data=data,
            headers={"Referer": "https://federatedauth.coventry.ac.uk/"},
        )
        if res.status_code != 200:
            raise AuthenticationFailure(
                "Failed to transfer to Aula, HTTP {}".format(res.status_code)
            )
        self.headers.update({"x-session-token": res.cookies.get("sso-session-t")})

    def __auth_engage(self):
        login_url = "https://engagementdashboard.coventry.ac.uk/login"

        res = Session.get(self, login_url)
        soup = BeautifulSoup(res.text, "lxml")

        hidden = soup.find("input", {"name": "_csrf"})["value"]
        payload = {
            "username": self.username,
            "password": self.password,
            "_csrf": hidden,
        }
        self.post(login_url, data=payload)

    def __auth_moodle(self):
        login_url = "https://cumoodle.coventry.ac.uk/login/index.php"

        res = Session.get(self, login_url)
        soup = BeautifulSoup(res.text, "lxml")
        token = soup.find("input", {"name": "logintoken"})["value"]

        data = {
            "username": self.username,
            "password": self.password,
            "logintoken": token,
        }
        res = Session.post(self, login_url, data=data)

        if res.status_code != 200:
            raise AuthenticationFailure(
                "Failed to load Moodle, HTTP {}".format(res.status_code)
            )

    domainRegex = re.compile(r"https?://([\w.\-]+)")
    authHandler = {
        "webapp.coventry.ac.uk": __auth_sonic,
        "engagementdashboard.coventry.ac.uk": __auth_engage,
        "coventry.kuali.co": __auth_kuali,
        "cumoodle.coventry.ac.uk": __auth_moodle,
        "apiv2.coventry.aula.education": __auth_aula,
    }
    redirectPages = [
        "https://engagementdashboard.coventry.ac.uk/login",
        "https://cumoodle.coventry.ac.uk/login/index.php",
    ]

    def __init__(self, username: str, password: str):
        Session.__init__(self)

        self.username = username
        self.password = password

    def __run_handler(self, res: Response):
        domain = self.domainRegex.search(res.url)
        if domain:
            domain = domain.group(1)
            try:
                func = self.authHandler[domain]
                func(self)
            except KeyError:
                pass

    def get(self, url: str, *args: [str], **kwargs: [str]):
        # print( url )
        # certfile = os.path.join('/etc/ssl/certs/','ca-bundle.crt')

        res = Session.get(self, url, verify=False, *args, **kwargs)

        if self.__fail_condition(
            res
        ):  # if the page failed or we got redirected to anything in redirectPages
            self.__run_handler(res)

            res = Session.get(self, url, *args, **kwargs)

        if self.__fail_condition(res):  # if it still didn't work give up
            raise AuthenticationFailure("Could not authenticate")

        return res

    def post(self, url: str, *args: [str], **kwargs: [str]):
        res = Session.post(self, url, *args, **kwargs)

        if self.__fail_condition(
            res
        ):  # if the page failed or we got redirected to anything in redirectPages
            self.__run_handler(res)
            res = Session.post(self, url, *args, **kwargs)

        if self.__fail_condition(res):  # if it still didn't work give up
            raise AuthenticationFailure("Could not authenticate")

        return res


def url_safe(val: str | bytes):
    return parse.quote(val, safe="")


if __name__ == "__main__":
    auth = Authenticator(sys.argv[1], sys.argv[2])

    response = auth.get(
        "https://cumoodle.coventry.ac.uk/grade/report/grader/index.php?id=47437"
    )
    # response = auth.get("https://apiv2.coventry.aula.education/users/getBySessionToken")
    print(response.text)
    print()

    # response = auth.get("https://webapp.coventry.ac.uk/Timetable-main")
    # print(response)

    # response = auth.get("https://engagementdashboard.coventry.ac.uk/attendance/all?id=7203071")
    # print(response)
