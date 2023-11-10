import metadata
import db_object_read




if __name__ == "__main__":

    # process the database objects csv file
    csv_filepath = "../../examples/r102_objects.csv"
    origin = metadata.Origin(name="R102", description="R102 oracle database instance", type=metadata.OriginType.ORACLE_DB)
    objects = db_object_read.get_oracle_objects_from_csv(origin=origin,
                                        csv_filepath=csv_filepath)

    idx = db_object_read.generate_index(objects)

    # process the origin code
    root_dir = "../../examples/PortalTC-Core-master"
    owner_filter = 'A_RAIABD'  # the database owner of the objects to be analyzed through the source code


