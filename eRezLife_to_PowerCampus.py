import csv
import os
import sys
import datetime as dt
import requests
import urllib3
from loguru import logger
from pathlib import WindowsPath
from sqlalchemy import MetaData, Table
from sqlalchemy import update, select, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker


import local_db


logger.add(sys.stdout, level="WARNING")
logger.add(sys.stderr, level="WARNING")
logger.add(
    "logs/eRezLife_to_PowerCampus.log",
    rotation="monthly",
    format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {name} | {message}",
    level="INFO",
)


def download_file()  -> str:

    today = dt.datetime.today()
    today_str = today.strftime("%Y%m%d_%H%M")

    app_path = WindowsPath(r"\\psc-data\E\Applications\ResidenceLife\eRezLife")
    # app_path = WindowsPath(r"E:\Applications\ResidenceLife\eRezLife")
    data_path = app_path / "Files"
    downloads_path = data_path / "downloads"
    export_file = downloads_path / f"powercampus_export_{today_str}.csv"
    logger.debug(f"{export_file=}")

    export_token = os.environ.get("eRezLife_EXPORT_TOKEN")
    logger.debug(f"{export_token=}")

    urllib3.disable_warnings()
    request_url = ( "https://paulsmiths.erezlife.com/app/one.php?" +
                "manager=exportView&purpose=export&export_class=residenceApplicationExportSpec" +
                f"&token={export_token}"
    )
    logger.debug(request_url)
    with requests.get(request_url, verify=False ) as r:
        logger.debug(f"{r.status_code=}")
        r.raise_for_status()
    
        with open(export_file, 'wb') as f:
            chars = 0
            for line in r.iter_lines():
                chars += f.write(line + '\n'.encode())
    logger.info(f"file written: {export_file} ({chars})")
    
    return export_file



def main():
    logger.info(f"eRezLife_to_PowerCampus Start: {dt.datetime.now()}")

    logger.info(f"Begin: download_files()")
    csv_filename = download_file()
    logger.debug(f"download file: {csv_filename}")
    logger.info(f"End: download_files()")

    connection = local_db.connection(test=True)
    engine = connection.engine
    Session = sessionmaker(engine)
    metadata = MetaData()
    residency = Table('RESIDENCY', metadata, autoload=True, autoload_with=engine)

    with open(csv_filename, encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        new_rec_count = 0
        updated_rec_count = 0
        for row in reader:
            year, term  = row['Session ERP/SIS term code'].split('.')
            term = term.upper()
            student_id = row['Student ID']
            logger.debug(f"{row['Student ID']} {year} {term}")
            if (row['Application status']=='Accepted Offer'):
                new_building = row['building_code']
                new_room = row['room_id']
                logger.debug(f"{year=}, {term=}, {student_id=}, {new_building=}, {new_room=}")
                with Session() as session:
                    # check for existing record
                    result = ( session.query(residency)
                            .filter(residency.c.PEOPLE_CODE_ID == student_id)
                            .filter(residency.c.ACADEMIC_YEAR == year)
                            .filter(residency.c.ACADEMIC_TERM == term)
                            .first()
                    )
                    if not result:
                        logger.info(f"Create record: {student_id=}, {year=}, {term=}, ")
                        create_sql = f"exec dbo.sp_create_residency '{student_id}','{year}','{term}','MAIN','eRezLife','0001'"
                        try:
                            session.execute(create_sql)
                            session.commit()
                            new_rec_count += 1
                        except IntegrityError as error:
                            logger.error(f"Create {student_id}: {create_sql}")
                            logger.error(error)                    
                        current_building = None
                        current_room = None
                    else:
                        current_building = result[10]
                        current_room = result[11]
                        logger.debug(f"Existing record: {student_id=}, {current_building=}, {current_room=}")
                    
                    # update building, room
                    if (new_building != current_building) or (new_room != current_room):
                        logger.info(f"Updating: {student_id=}, {year=}, {term=}, {new_building=}, {new_room=}")
                        u = update(residency).where(
                            and_(
                                residency.c.PEOPLE_CODE_ID == student_id,
                                residency.c.ACADEMIC_YEAR == year,
                                residency.c.ACADEMIC_TERM == term,
                                residency.c.ACADEMIC_SESSION == 'MAIN'
                            )
                        )
                        u = u.values(
                            RESIDENT_COMMUTER='R',
                            FOOD_PLAN='STAN',
                            DORM_PLAN='ROOM',
                            DORM_CAMPUS='O000000001',
                            DORM_BUILDING=new_building,
                            DORM_ROOM=new_room
                        )
                        logger.debug(u.compile(engine))
                        
                        try:
                            session.execute(u)
                            session.commit()
                            updated_rec_count += 1
                        except IntegrityError as error:
                            logger.error(f"Update {student_id}: {u.compile(engine)}")
                            logger.error(error)                    

        logger.info(f"Records created: {new_rec_count}, Records updated: {updated_rec_count}")

    logger.info(f"eRezLife_to_PowerCampus End: {dt.datetime.now()}")


if __name__ == "__main__":
    logger.info(f"cwd: {os.getcwd()}")
    main()
