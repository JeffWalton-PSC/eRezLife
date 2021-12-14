import os
import sys
import datetime as dt
import pandas as pd
import pysftp
from loguru import logger
from pathlib import WindowsPath

import powercampus as pc


logger.add(sys.stderr, level="WARNING")
logger.add(
    "logs/eRezLife.log",
    rotation="monthly",
    format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {name} | {message}",
    level="INFO",
)

app_path = WindowsPath(r"E:\Applications\ResidenceLife\eRezLife")
data_path = app_path / "Files"
studentlists_path = data_path / "studentlists"
studentpics_path = data_path / "studentpics"
output_file = studentlists_path / "residence_applicants.csv"
image_path = WindowsPath(r"E:\Applications\Starfish\Files\prod\sisdatafiles\studentFiles\studentPhotos")
    

def create_dataframe() -> pd.DataFrame:
    """
    Creates eRezLife DataFrame.
    """

    current_yt_df = pc.current_yearterm()
    current_term = current_yt_df['term'].iloc[0]
    current_year = current_yt_df['year'].iloc[0]
    current_yt = current_yt_df['yearterm'].iloc[0]
    current_yt_sort = current_yt_df['yearterm_sort'].iloc[0]


    academic = pc.select("ACADEMIC", 
        fields=['PEOPLE_CODE_ID', 'ACADEMIC_YEAR', 'ACADEMIC_TERM', 'ADMIT_YEAR', 'ADMIT_TERM'],
        where=f"ACADEMIC_YEAR>='{int(current_year)}' and ACADEMIC_TERM IN ('FALL', 'SPRING') and ACADEMIC_SESSION=''" +
            "and PRIMARY_FLAG='Y' and CREDITS>0 and CURRICULUM<>'ADVST' and PROGRAM='U'" + 
            "and ADMIT_YEAR IS NOT NULL", 
        )
    academic = pc.add_col_yearterm(academic)
    academic = pc.add_col_yearterm_sort(academic)
    academic['yearterm_sort'] = academic['yearterm_sort'].astype(int)
    yearterms_to_keep = tuple(academic[['yearterm', 'yearterm_sort']].groupby(['yearterm_sort']).first().reset_index().nlargest(4,['yearterm_sort'])['yearterm'])
    academic = academic.loc[(academic['yearterm'].isin(yearterms_to_keep)),:]
    academic = (academic[['PEOPLE_CODE_ID', 'ACADEMIC_YEAR', 'ACADEMIC_TERM', 'yearterm', 'yearterm_sort', 'ADMIT_YEAR', 'ADMIT_TERM', ]]
                .groupby(['PEOPLE_CODE_ID', 'ACADEMIC_YEAR', 'ACADEMIC_TERM'])
                .first()
                .reset_index()
                )
    academic['admit_yearterm'] = academic['ADMIT_YEAR'] + '.' +  academic['ADMIT_TERM'].str.title()
    academic = academic.loc[(academic['yearterm_sort']>=int(current_yt_sort))]
     

    people = pc.select('PEOPLE',
        fields=['PEOPLE_CODE_ID', 'FIRST_NAME', 'LAST_NAME', 'PrimaryEmailId', 'DisplayName', 'BIRTH_DATE', 'PersonId' ],
        where="DECEASED_FLAG<>'Y' and BIRTH_DATE>'1900-01-01' and BIRTH_DATE<'2500-01-01'",
        )
    people['PrimaryEmailId'] = people['PrimaryEmailId'].astype('UInt32')
    people['PersonId'] = people['PersonId'].astype('UInt32')
    people['BIRTH_DATE'] = pd.to_datetime(people['BIRTH_DATE']).dt.date

    demographics = pc.select('DEMOGRAPHICS',
        fields=['PEOPLE_CODE_ID', 'GENDER', ],
        where="ACADEMIC_YEAR='' and ACADEMIC_TERM='' and ACADEMIC_SESSION=''",
        )
    demographics['GENDER'] = demographics['GENDER'].astype('category')

    email = pc.select('EmailAddress',
        fields=['EmailAddressId', 'PeopleOrgCodeId', 'EmailType', 'Email', 'IsActive', ],
        where="IsActive=1 and EmailType='HOME'",
        )
    email['EmailAddressId'] = email['EmailAddressId'].astype('UInt32')

    cell_phone = pc.select('PersonPhone',
        fields=['PersonId', 'PhoneType', 'PhoneNumber', 'Revision_Date'],
        where="PhoneType='SCELL'",
        )
    cell_phone['PersonId'] = cell_phone['PersonId'].astype('UInt32')
    cell_phone = cell_phone.loc[cell_phone.reset_index().groupby('PersonId')['Revision_Date'].idxmax()]

    people = (people
        .merge(demographics,
            'left',
            on='PEOPLE_CODE_ID',
            )
        .merge(email.loc[:,['EmailAddressId', 'Email']],
            'inner',
            left_on='PrimaryEmailId',
            right_on='EmailAddressId',
            )
        .merge(cell_phone.loc[:,['PersonId', 'PhoneNumber']],
            'left',
            on='PersonId',
            )
        )
    
    students = (academic[['PEOPLE_CODE_ID', 'ACADEMIC_YEAR', 'ACADEMIC_TERM', 'yearterm', 'yearterm_sort', 'admit_yearterm']]
        .merge(people[['PEOPLE_CODE_ID', 'FIRST_NAME', 'LAST_NAME', 'DisplayName', 'GENDER', 'Email', 'BIRTH_DATE', 'PhoneNumber']],
            'left',
            on='PEOPLE_CODE_ID',
            )
        )
    students = students.loc[(students['Email'].notnull())]

    residency = pc.select('RESIDENCY',
        fields=['PEOPLE_CODE_ID', 'ACADEMIC_YEAR', 'ACADEMIC_TERM', 'ACADEMIC_SESSION', 
                'RESIDENT_COMMUTER', 'FOOD_PLAN', 'DORM_PLAN', 'DORM_BUILDING', 'DORM_ROOM',
                ],
        where=f"ACADEMIC_YEAR>='{int(current_year)}' and ACADEMIC_YEAR<'{int(current_year)+1}' and ACADEMIC_TERM IN ('FALL', 'SPRING') and ACADEMIC_SESSION=''",
        distinct=True
        )
    residency = pc.add_col_yearterm(residency)
    residency = pc.add_col_yearterm_sort(residency)
    residency['yearterm_sort'] =  residency['yearterm_sort'].astype(int)
    residency['rank'] = residency.groupby('PEOPLE_CODE_ID')['yearterm_sort'].rank("dense", ascending=False)
    residency = residency.loc[(residency['rank']<=3),
                              ['PEOPLE_CODE_ID', 'yearterm', 'yearterm_sort', 'ACADEMIC_YEAR', 'ACADEMIC_TERM', 'rank', 'RESIDENT_COMMUTER', 'FOOD_PLAN', 'DORM_PLAN', 'DORM_BUILDING', 'DORM_ROOM']
                              ]
 
    students = (students
        .merge(residency[['PEOPLE_CODE_ID', 'ACADEMIC_YEAR', 'ACADEMIC_TERM', 'RESIDENT_COMMUTER', 'FOOD_PLAN', 'DORM_PLAN', 'DORM_BUILDING', 'DORM_ROOM']],
            'left',
            on=['PEOPLE_CODE_ID', 'ACADEMIC_YEAR', 'ACADEMIC_TERM'],
            )
        )
    students['username'] = students['Email'].str.split('@').str[0]
    students = (
        students.sort_values(['PEOPLE_CODE_ID', 'yearterm_sort'])
                .rename(columns={
                    'PEOPLE_CODE_ID': 'student_id',
                    'DisplayName': 'first_name',
                    'LAST_NAME': 'last_name',
                    'Email': 'email',
                    'username': 'external_auth_id',
                    'yearterm': 'term',
                    'DORM_BUILDING': 'building',
                    'DORM_ROOM': 'room',
                    'GENDER': 'gender',
                    'admit_yearterm': 'admit_term',
                    'BIRTH_DATE': 'birthdate',
                    'PhoneNumber': 'cell'
            }
                )
                .drop(
                    [
                        'FIRST_NAME',
                        'RESIDENT_COMMUTER',
                        'FOOD_PLAN',
                        'DORM_PLAN',
                    ],
                    axis=1,
                )
            )
    students['session'] = students['term']

    field_list = [
        'student_id',
        'first_name',
        'last_name',
        'email',
        'external_auth_id',
        'session',
        'term',
        # 'building',
        # 'room',
        'gender',
        'admit_term',
        'birthdate',
        'cell',
        ]
    students = students[field_list]

    return students


def sftp_connection():
    """
    Establishes remote SFTP connection.
    """

    hn = "sftp.us.erezlife.com"
    logger.info(f'SFTP connection: {hn=}')
    un = os.environ.get("eRezLife_username")
    logger.info(f'SFTP connection: {un=}')
    pk = app_path / ".ssh" / "private_key_eRezLife.key"
    # logger.debug(f"private_key: {pk=}")
    pkp = os.environ.get("eRezLife_pkp")
    # logger.debug(f'SFTP connection: {pkp=}')
    known_hosts = app_path / ".ssh" / "sftp.us.erezlife.com_hostkey.key"
    cnopts = pysftp.CnOpts(knownhosts=known_hosts)
    cnopts.hostkeys.load(known_hosts)

    return pysftp.Connection(host=hn, username=un, private_key=pk, private_key_pass=pkp, cnopts=cnopts)


def upload_files() -> None:
    """
    Uploads files to eRezLife via SFTP.
    """

    with sftp_connection() as sftp:
        with sftp.cd('studentlists'):
            logger.info(f'SFTP remote cwd: {sftp.getcwd()}')
            sftp.put(studentlists_path / 'residence_applicants.csv')
            logger.info(f"SFTP upload file name: {(studentlists_path / 'residence_applicants.csv')}")
            for attr in sftp.listdir_attr():
                logger.info(f'SFTP remote file attr: {attr}')
        sftp.close()
    return


def upload_student_photos(students: list) -> None:
    """
    Given a list of student id numbers, copies new photos to 'studentpics' directory and uploads to SFTP site.
    """
    import shutil

    new = 0
    with sftp_connection() as sftp:
        with sftp.cd('studentpics'):
            logger.info(f'SFTP remote cwd: {sftp.getcwd()}')
            logger.info(f"SFTP picture path: {studentpics_path}")
            for s in students:
                file_from = WindowsPath(image_path / (s + '.jpg'))
                if file_from.is_file():
                    file_to = WindowsPath(studentpics_path / (s + '.jpg'))
                    if (not file_to.exists()):
                        new += 1
                        shutil.copyfile(file_from, file_to)
                        logger.info(f"{file_from=} {file_to=}")
                        sftp.put(file_to)
                    elif (file_from.exists() and file_to.exists()):
                        if (os.path.getmtime(file_from) > os.path.getmtime(file_to)):
                            new += 1
                            shutil.copyfile(file_from, file_to)
                            logger.info(f"{file_from=} {file_to=}")
                            sftp.put(file_to)

        sftp.close()
        logger.info(f'new student pictures: {new}')
    return


def main():
    logger.info(f'eRezLife Start: {dt.datetime.now()}')

    df = create_dataframe()
    df.to_csv(output_file, index=False)
    logger.info(f'file written: {df.shape} {output_file}')

    logger.info(f'Begin: upload_files()')
    upload_files()
    logger.info(f'End: upload_files()')

    student_ids = list(df['student_id'].unique())
    logger.info(f'unique student id records in file: {len(student_ids)}')

    logger.info(f'Begin: upload_student_photos()')
    new_pics = upload_student_photos(student_ids)
    logger.info(f'End: upload_student_photos()')
    
    logger.info(f'eRezLife End: {dt.datetime.now()}')


if __name__ == "__main__":
    logger.info(f'cwd: {os.getcwd()}')
    main()

