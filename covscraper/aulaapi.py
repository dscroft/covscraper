import sys

from requests import Session

from covscraper.auth import Authenticator


def email_to_id(session: Session, student_email: str):
    # Nuke @uni. in case it got copied in
    student_email = student_email.replace("@uni.", "@")

    # Grab internal aula id for student first
    aula_id = session.get(
        "https://apiv2.coventry.aula.education/search/v2/users/{}?size=1".format(
            student_email
        ),
    ).json()["users"][0]["id"]

    # Grab student object and extract corresponding student ID
    data = {"userIds": [aula_id]}
    return session.post(
        "https://apiv2.coventry.aula.education/users/getByIds",
        json=data,
    ).json()["users"][0]["custom"]["studentId"]


if __name__ == "__main__":
    auth = Authenticator(sys.argv[1], sys.argv[2])
    print(email_to_id(auth, sys.argv[3]))
