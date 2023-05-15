import sys

from requests import Session

from covscraper.auth import Authenticator


def email_to_id(session: Session, student_email: str):
    # Nuke @uni. in case it got copied in
    student_email = student_email.replace("@uni.", "@")

    # Grab internal aula id for student first
    response = session.get(
        "https://apiv2.coventry.aula.education/search/v2/users/{}".format(
            student_email
        ),
    )

    aula_id = None
    for i in response.json()["users"]:
        if i["email"] == student_email:
            aula_id = i["id"]
            break

    # Grab student object and extract corresponding student ID
    data = {"userIds": [aula_id]}
    return session.post(
        "https://apiv2.coventry.aula.education/users/getByIds",
        json=data,
    ).json()["users"][0]["custom"]["studentId"]


if __name__ == "__main__":
    auth = Authenticator(sys.argv[1], sys.argv[2])
    print(email_to_id(auth, sys.argv[3]))
