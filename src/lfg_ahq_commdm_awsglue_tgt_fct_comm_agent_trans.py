import sys
import boto3
import json
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext, SparkConf
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import *
from pyspark.sql.functions import *
from datetime import datetime
from connect import *



## @params: [destinationbucket, JOB_NAME]
args = getResolvedOptions(sys.argv, ['destinationbucket','JOB_NAME','paramfilename','odsschemaname','rsschemaname','orajdbcdrivername','rsdbdatabase','rsdbtgttblname','rscatalogconn','rscatalogtablename','rscatalogdatabase','odssecretname','conffilename','confbucketname','confsubdir','rssecretname'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)


work_dir = "/tmp/glue/"
region_name='us-east-1'
os.makedirs(work_dir)
os.chdir(work_dir)
print(os.getcwd())

##generating current time
time=datetime.utcnow()
v_start_time=time.strftime("%Y-%m-%d %H:%M:%S")

##defining variables
param_file_name=args['paramfilename']
conf_bucket=args['confbucketname']
sub_dir=args['confsubdir']
s3_bucket=conf_bucket.split(',')[0]
param_var=get_config(param_file_name,s3_bucket,region_name,sub_dir)
print(param_var)

v_src_sys = param_var['param_src_sys']
batch_date=param_var['param_batch_date']
mart_batch_id=param_var["param_mart_batch_id"]
ods_batch_id=param_var["param_ods_batch_id"]
dim_dt_id=param_var["param_dim_dt_id"]

default_dim_prod_cvt=param_var['default_dim_prod_cvt']
default_dim_prod_fwv=param_var['default_dim_prod_fwv']
default_dim_plcy_rdr_cvt=param_var['default_dim_plcy_rdr_cvt']
default_dim_plcy_rdr_fwv=param_var['default_dim_plcy_rdr_fwv']
default_ln_of_bus_cvt=param_var['default_ln_of_bus_cvt']
default_ln_of_bus_fwv=param_var['default_ln_of_bus_fwv']
default_dim_plcy_cvt=param_var['default_dim_plcy_cvt']
default_dim_plcy_fwv=param_var['default_dim_plcy_fwv']
default_dim_agent_dist_chnl=param_var['default_dim_agent_dist_chnl']
default_dim_agent=param_var['default_dim_agent']
dim_comm_policy_lowerbound=param_var['dim_comm_policy_lowerbound']
dim_comm_policy_upperbound=param_var['dim_comm_policy_upperbound']
dim_policy_lowerbound=param_var['dim_policy_lowerbound']
dim_policy_upperbound=param_var['dim_policy_upperbound']
dim_ln_of_bus_lowerbound=param_var['dim_ln_of_bus_lowerbound']
dim_ln_of_bus_upperbound=param_var['dim_ln_of_bus_upperbound']
dim_prod_lowerbound=param_var['dim_prod_lowerbound']
dim_prod_upperbound=param_var['dim_prod_upperbound']
dim_policy_rider_lowerbound=param_var['dim_policy_rider_lowerbound']
dim_policy_rider_upperbound=param_var['dim_policy_rider_upperbound']
dim_agent_lowerbound=param_var['dim_agent_lowerbound']
dim_agent_upperbound=param_var['dim_agent_upperbound']
dim_trans_lowerbound=param_var['dim_trans_lowerbound']
dim_comm_trans_upperbound=param_var['dim_comm_trans_upperbound']
dim_comm_trans_lowerbound=param_var['dim_comm_trans_lowerbound']
dim_trans_upperbound=param_var['dim_trans_upperbound']
dim_agent_dist_chnl_lowerbound=param_var['dim_dist_chnl_lowerbound']
dim_agent_dist_chnl_upperbound=param_var['dim_dist_chnl_upperbound']
dim_dt_lowerbound=param_var['dim_dt_lowerbound']
dim_dt_upperbound=param_var['dim_dt_upperbound']
fct_comm_agent_trans_lowerbound=param_var['fct_comm_agent_trans_lowerbound']
fct_comm_agent_trans_upperbound=param_var['fct_comm_agent_trans_upperbound']
print(fct_comm_agent_trans_upperbound)

v_ods_schema = args['odsschemaname']
v_redshift_schema_name = args['rsschemaname']
v_job_name = args['JOB_NAME']
jdbc_driver_name=args['orajdbcdrivername']
redshift_db=args['rsdbdatabase']
redshift_cata_tbl_nm=args['rscatalogtablename']
rs_catalog_conn=args['rscatalogconn']
rs_db_tbl=args['rsdbtgttblname']
rs_database=args['rscatalogdatabase']
secret_name=args['odssecretname']
redshift_secret=args['rssecretname']
conf_file=args['conffilename']
print("arguments retrieved")

conf_file_name=conf_file.split(',')[0]
config_var=get_config(conf_file_name,s3_bucket,region_name,sub_dir)

num_of_partitions =config_var['fct_comm_agent_trans']['numPartitions']
dim_prod_partition=config_var['fct_comm_agent_trans']['dim_prod_partition']
dim_ln_of_bus_partition=config_var['fct_comm_agent_trans']['dim_ln_of_bus_partition']
dim_policy_rider_partition=config_var['fct_comm_agent_trans']['dim_policy_rider_partition']
dim_policy_partition=config_var['fct_comm_agent_trans']['dim_policy_partition']
dim_comm_policy_partition=config_var['fct_comm_agent_trans']['dim_comm_policy_partition']
dim_trans_partition=config_var['fct_comm_agent_trans']['dim_trans_partition']
dim_agent_dist_chnl_partition=config_var['fct_comm_agent_trans']['dim_agent_dist_chnl_partition']
dim_comm_trans_partition=config_var['fct_comm_agent_trans']['dim_comm_trans_partition']
dim_agent_partition=config_var['fct_comm_agent_trans']['dim_agent_partition']
dim_date_partition=config_var['fct_comm_agent_trans']['dim_date_partition']
fct_comm_agent_trans_partition=config_var['fct_comm_agent_trans']['fct_comm_agent_trans_partition']

dim_comm_pol_fltr=config_var['fct_comm_agent_trans']['dim_comm_pol_fltr']
dim_pol_fltr=config_var['fct_comm_agent_trans']['dim_pol_fltr']
dim_prod_fltr=config_var['fct_comm_agent_trans']['dim_prod_fltr']
dim_ln_of_bus_filter=config_var['fct_comm_agent_trans']['dim_ln_of_bus_filter']
dim_policy_rider_filter=config_var['fct_comm_agent_trans']['dim_policy_rider_filter']
dim_trans_filter=config_var['fct_comm_agent_trans']['dim_trans_filter']
dim_agent_filter=config_var['fct_comm_agent_trans']['dim_agent_filter']
dim_agent_dist_chnl_filter=config_var['fct_comm_agent_trans']['dim_agent_dist_chnl_filter']
dim_date_filter=config_var['fct_comm_agent_trans']['dim_date_filter']
dim_comm_trans_filter=config_var['fct_comm_agent_trans']['dim_comm_trans_filter']
fct_comm_agent_trans_filter=config_var['fct_comm_agent_trans']['fct_comm_agent_trans_filter']
POSTACTIONS0=config_var['fct_comm_agent_trans']['post-actions']


ods_query0=config_var["fct_comm_agent_trans"]["ods_query"]
ods_query=ods_query0.format(v_ods_schema,mart_batch_id,ods_batch_id,v_src_sys)
print("------------")
print(ods_query)


map_logic=config_var["fct_comm_agent_trans"]["ods_map"]
ods_map=list(map_logic.split('*'))
print(ods_map)
trans_map = [eval(ele) for ele in ods_map]
print(trans_map)
select_fields = config_var["fct_comm_agent_trans"]["ods_select_fields"]
ods_select_fields = [eval(ele) for ele in select_fields.split(',')]
print(ods_select_fields)
dup_check=config_var['fct_comm_agent_trans']['dup_check']
dup_check=dup_check.format(v_redshift_schema_name)
map_logic=config_var["fct_comm_agent_trans"]["map"]
final_map=list(map_logic.split('*'))
print(final_map)
mapping = [eval(ele) for ele in final_map]
print(mapping)
select_fields = config_var["fct_comm_agent_trans"]["select_fields"]
final_select_fields = [eval(ele) for ele in select_fields.split(',')]
print(final_select_fields)

oracle_key=get_secret(secret_name,region_name)
username=oracle_key['username']
password=oracle_key['password']
host=oracle_key['host']
port=oracle_key['port']
dbname=oracle_key['dbname']
url=str("jdbc:oracle:thin://@")+str(host)+":"+str(port)+"/"+str(dbname)
print("got secret")

redshift_key=get_secret(redshift_secret,region_name)
redshift_db_host=redshift_key['host']
redshift_db_name=redshift_key['dbname']
redshift_db_port=redshift_key['port']
redshift_db_user=redshift_key['username']
redshift_db_pass=redshift_key['password']
print("redshift key retrieved")

cert_file_nm=conf_file.split(',')[1]
conf_bucketname=conf_bucket.split(',')[1]
cert_download(cert_file_nm,conf_bucketname,region_name)

try:
    JDBCURL = "jdbc:postgresql://{}:{}/{}?ssl=true&sslfactory=org.postgresql.ssl.NonValidatingFactory&sslpath={}{}" \
    .format(redshift_db_host,redshift_db_port,redshift_db_name,work_dir,cert_file_nm)
       
    print("Current batch data load started...")
    ## Def Read data dynamic frame using JDBC
    df = get_vw(glueContext,ods_query,jdbc_driver_name,url,username,password)
    print('get view is complete')

    ## Convert df to Glue dynamic frame
    src_dyn_frm = DynamicFrame.fromDF(df, glueContext, "src_dyn_frm")

    ## Apply map operation so Glue will understand its input and output mapping
    ods_applymapping= ApplyMapping.apply(frame = src_dyn_frm, mappings = trans_map \
                        ,transformation_ctx = "applymapping")
    print('ODS apply mapping is completed!')

    ## Select required fileds
    ods_selectfields = SelectFields.apply(frame = ods_applymapping, paths = ods_select_fields \
                        , transformation_ctx = "ods_selectfields")
    print('ODS selectfields completed!')

    df_ods=ods_selectfields.toDF()
    #df_ods.repartition(num_of_partitions)
    df_count=df_ods.count()
    print("Record count for ODS source data: " +str(df_count))
    ##Create ods temp view
    df_ods.createOrReplaceTempView("ODS_VW")
    print("ODS tmp view is completed!")
    
    dim_comm_pol_fltr=dim_comm_pol_fltr.format(v_redshift_schema_name,batch_date)
    df_comm_ply= spark.read.format("jdbc") \
        .option("url", JDBCURL) \
        .option("dbtable", dim_comm_pol_fltr) \
        .option("user", redshift_db_user) \
        .option("password", redshift_db_pass) \
        .option("driver", "org.postgresql.Driver") \
        .option("partitionColumn", dim_comm_policy_partition) \
        .option("numPartitions", num_of_partitions) \
        .option("lowerBound", dim_comm_policy_lowerbound) \
        .option("upperBound", dim_comm_policy_upperbound) \
        .load()
    #df_comm_ply.show()

    #dim_comm_ply=df_comm_ply.count()
    #print("Record count of Dim Commission policy: " +str(dim_comm_ply))
    
    df_comm_ply.createOrReplaceTempView("DIM_COMM_POL")
    print("DIM_COMM_POL tmp view is completed!")
    
    dim_pol_fltr=dim_pol_fltr.format(v_redshift_schema_name,batch_date)
    df_policy= spark.read.format("jdbc") \
        .option("url", JDBCURL) \
        .option("dbtable", dim_pol_fltr) \
        .option("user", redshift_db_user) \
        .option("password", redshift_db_pass) \
        .option("driver", "org.postgresql.Driver") \
        .option("partitionColumn", dim_policy_partition) \
        .option("numPartitions", num_of_partitions) \
        .option("lowerBound", dim_policy_lowerbound) \
        .option("upperBound", dim_policy_upperbound) \
        .load()
    #df_policy.show()

    #dim_policy=df_policy.count()
    #print("Record count of Dim Policy: " +str(dim_policy))
    
    df_policy.createOrReplaceTempView("DIM_POLICY")
    print("DIM_POLICY tmp view is completed!")
    
    
    dim_prod_fltr=dim_prod_fltr.format(v_redshift_schema_name,batch_date)
    df_prod= spark.read.format("jdbc") \
        .option("url", JDBCURL) \
        .option("dbtable", dim_prod_fltr) \
        .option("user", redshift_db_user) \
        .option("password", redshift_db_pass) \
        .option("driver", "org.postgresql.Driver") \
        .option("partitionColumn", dim_prod_partition) \
        .option("numPartitions", num_of_partitions) \
        .option("lowerBound", dim_prod_lowerbound) \
        .option("upperBound", dim_prod_upperbound) \
        .load()
    #df_prod.show()

    #dim_prod=df_prod.count()
    #print("Record count of Dim Prod: " +str(dim_prod))
    
    df_prod.createOrReplaceTempView("DIM_PROD")
    print("DIM_PROD tmp view is completed!")
    
    dim_ln_of_bus_filter=dim_ln_of_bus_filter.format(v_redshift_schema_name,batch_date)
    df_ln_bus= spark.read.format("jdbc") \
        .option("url", JDBCURL) \
        .option("dbtable", dim_ln_of_bus_filter) \
        .option("user", redshift_db_user) \
        .option("password", redshift_db_pass) \
        .option("driver", "org.postgresql.Driver") \
        .option("partitionColumn", dim_ln_of_bus_partition) \
        .option("numPartitions", num_of_partitions) \
        .option("lowerBound", dim_ln_of_bus_lowerbound) \
        .option("upperBound", dim_ln_of_bus_upperbound) \
        .load()
    #df_ln_bus.show()

    #dim_ln_of_bus=df_ln_bus.count()
    #print("Record count of Dim LN OF BUS: " +str(dim_ln_of_bus))
    
    df_ln_bus.createOrReplaceTempView("DIM_LN_OF_BUS")
    print("DIM_LN_OF_BUS tmp view is completed!")

    dim_policy_rider_filter=dim_policy_rider_filter.format(v_redshift_schema_name,batch_date)
    df_ply_rdr= spark.read.format("jdbc") \
        .option("url", JDBCURL) \
        .option("dbtable", dim_policy_rider_filter) \
        .option("user", redshift_db_user) \
        .option("password", redshift_db_pass) \
        .option("driver", "org.postgresql.Driver") \
        .option("partitionColumn", dim_policy_rider_partition) \
        .option("numPartitions", num_of_partitions) \
        .option("lowerBound", dim_policy_rider_lowerbound) \
        .option("upperBound", dim_policy_rider_upperbound) \
        .load()
    #df_ply_rdr.show()

    #dim_ply_rdr=df_ply_rdr.count()
    #print("Record count of Dim Policy rider: " +str(dim_ply_rdr))
    
    df_ply_rdr.createOrReplaceTempView("DIM_POLICY_rider")
    print("DIM_POLICY_rider tmp view is completed!")
    
    dim_agent_filter=dim_agent_filter.format(v_redshift_schema_name,batch_date)
    df_agent= spark.read.format("jdbc") \
        .option("url", JDBCURL) \
        .option("dbtable", dim_agent_filter) \
        .option("user", redshift_db_user) \
        .option("password", redshift_db_pass) \
        .option("driver", "org.postgresql.Driver") \
        .option("partitionColumn", dim_agent_partition) \
        .option("numPartitions", num_of_partitions) \
        .option("lowerBound", dim_agent_lowerbound) \
        .option("upperBound", dim_agent_upperbound) \
        .load()
    #df_agent.show()

    #dim_agent=df_agent.count()
    #print("Record count of Dim Agent: " +str(dim_agent))
    
    df_agent.createOrReplaceTempView("DIM_AGENT")
    print("DIM_AGENT tmp view is completed!")
    
    dim_trans_filter=dim_trans_filter.format(v_redshift_schema_name)
    df_trans= spark.read.format("jdbc") \
        .option("url", JDBCURL) \
        .option("dbtable", dim_trans_filter) \
        .option("user", redshift_db_user) \
        .option("password", redshift_db_pass) \
        .option("driver", "org.postgresql.Driver") \
        .option("partitionColumn", dim_trans_partition) \
        .option("numPartitions", num_of_partitions) \
        .option("lowerBound", dim_trans_lowerbound) \
        .option("upperBound", dim_trans_upperbound) \
        .load()
    #df_trans.show()

    #dim_trans=df_trans.count()
    #print("Record count of DIM_TRANS: " +str(dim_trans))
    
    df_trans.createOrReplaceTempView("DIM_TRANS")
    print("DIM_TRANS tmp view is completed!")
        
    dim_comm_trans_filter=dim_comm_trans_filter.format(v_redshift_schema_name)
    df_comm_trans= spark.read.format("jdbc") \
        .option("url", JDBCURL) \
        .option("dbtable", dim_comm_trans_filter) \
        .option("user", redshift_db_user) \
        .option("password", redshift_db_pass) \
        .option("driver", "org.postgresql.Driver") \
        .option("partitionColumn", dim_comm_trans_partition) \
        .option("numPartitions", num_of_partitions) \
        .option("lowerBound", dim_comm_trans_lowerbound) \
        .option("upperBound", dim_comm_trans_upperbound) \
        .load()
    #df_comm_trans.show()

    #dim_comm_trans=df_comm_trans.count()
    #print("Record count of DIM_COMM_TRANS: " +str(dim_comm_trans))
    
    df_comm_trans.createOrReplaceTempView("DIM_COMM_TRANS")
    print("DIM_COMM_TRANS tmp view is completed!")
    
    
    dim_date_filter=dim_date_filter.format(v_redshift_schema_name)
    df_date= spark.read.format("jdbc") \
        .option("url", JDBCURL) \
        .option("dbtable", dim_date_filter) \
        .option("user", redshift_db_user) \
        .option("password", redshift_db_pass) \
        .option("driver", "org.postgresql.Driver") \
        .option("partitionColumn", dim_date_partition) \
        .option("numPartitions", num_of_partitions) \
        .option("lowerBound", dim_dt_lowerbound) \
        .option("upperBound", dim_dt_upperbound) \
        .load()
    #df_date.show()

    #dim_date=df_date.count()
    #print("Record count of dim_date: " +str(dim_date))
    
    df_date.createOrReplaceTempView("DIM_DATE")
    print("DIM_DATE tmp view is completed!")
    
    dim_agent_dist_chnl_filter=dim_agent_dist_chnl_filter.format(v_redshift_schema_name,batch_date)
    df_agent_dist_chnl= spark.read.format("jdbc") \
        .option("url", JDBCURL) \
        .option("dbtable", dim_agent_dist_chnl_filter) \
        .option("user", redshift_db_user) \
        .option("password", redshift_db_pass) \
        .option("driver", "org.postgresql.Driver") \
        .option("partitionColumn", dim_agent_dist_chnl_partition) \
        .option("numPartitions", num_of_partitions) \
        .option("lowerBound", dim_agent_dist_chnl_lowerbound) \
        .option("upperBound", dim_agent_dist_chnl_upperbound) \
        .load()
    #df_agent_dist_chnl.show()

    #dim_agent_dist_chnl=df_agent_dist_chnl.count()
    #print("Record count of DIM_AGENT_DIST_CHNL: " +str(dim_agent_dist_chnl))
    
    df_agent_dist_chnl.createOrReplaceTempView("DIM_AGENT_DIST_CHNL")
    print("DIM_AGENT_DIST_CHNL tmp view is completed!")
    
    fct_comm_agent_trans_filter=fct_comm_agent_trans_filter.format(v_redshift_schema_name)
    df_comm_agent_trans= spark.read.format("jdbc") \
        .option("url", JDBCURL) \
        .option("dbtable", fct_comm_agent_trans_filter) \
        .option("user", redshift_db_user) \
        .option("password", redshift_db_pass) \
        .option("driver", "org.postgresql.Driver") \
        .option("partitionColumn", fct_comm_agent_trans_partition) \
        .option("numPartitions", num_of_partitions) \
        .option("lowerBound", fct_comm_agent_trans_lowerbound) \
        .option("upperBound", fct_comm_agent_trans_upperbound) \
        .load()
    #df_comm_agent_trans.show()

    #fct_comm_agent_trans=df_comm_agent_trans.count()
    #print("Record count of Fct Comm Agent Trans : " +str(fct_comm_agent_trans))
    
    df_comm_agent_trans.createOrReplaceTempView("FCT_COMM_AGENT_TRANS")
    print("FCT_COMM_AGENT_TRANS tmp view is completed!")
    
    result_query=config_var["fct_comm_agent_trans"]["result_query"]
    print(result_query)
    result_query=result_query.format(default_dim_plcy_fwv,default_dim_plcy_cvt, \
            default_dim_prod_fwv, default_dim_prod_cvt,default_ln_of_bus_fwv,\
            default_ln_of_bus_cvt,default_dim_plcy_rdr_fwv,default_dim_plcy_rdr_cvt, \
            default_dim_agent_dist_chnl,default_dim_agent,v_src_sys)
    result_tb=spark.sql(result_query)
    #result_tb.repartition(num_of_partitions)
    #result_tb.show()
    
    ## Convert df to Glue dynamic frame
    src_dyn_frm1 = DynamicFrame.fromDF(result_tb, glueContext, "src_dyn_frm1")

    ## Apply map operation so Glue will understand its input and output mapping
    applymapping_tm = ApplyMapping.apply(frame = src_dyn_frm1, mappings = mapping \
                    , transformation_ctx = "applymapping_tm")

    print('View apply mapping is completed')

    ## Select required fileds
    selectfields_tm = SelectFields.apply(frame = applymapping_tm, paths = final_select_fields \
                    , transformation_ctx = "selectfields_tm")

    print('Final selectfields is completely mapped!')
    
    new_df=selectfields_tm.toDF()
    
    #new_df.repartition(num_of_partitions)
    new_df.createOrReplaceTempView("Dim_VW")
    print("DIM tmp view is completed!")
    
    final_query=config_var["fct_comm_agent_trans"]["final_query"]
    final_query=final_query.format(v_job_name)
    final_query_tb=spark.sql(final_query)
    #final_query_tb.repartition(num_of_partitions)
    #final_query_tb.show()
    
    src_dyn_frm2 = DynamicFrame.fromDF(final_query_tb, glueContext, "src_dyn_frm2")
    print(src_dyn_frm2)
    map_logic1=config_var["fct_comm_agent_trans"]["map_final"]
    final_map1=list(map_logic1.split('*'))
    print(final_map1)
    mapping1 = [eval(ele) for ele in final_map1]
    print(mapping1)
    select_fields1 = config_var["fct_comm_agent_trans"]["select_final_fields"]
    final_select_fields1 = [eval(ele) for ele in select_fields1.split(',')]
    print(final_select_fields1)
    
    
    
    applymapping_tm1= ApplyMapping.apply(frame = src_dyn_frm2, mappings = mapping1 \
                    , transformation_ctx = "applymapping_tm1")

    print('View apply mapping is completed')

    ## Select required fileds
    selectfields_tm1 = SelectFields.apply(frame = applymapping_tm1, paths = final_select_fields1 \
                    , transformation_ctx = "selectfields_tm1")

    print('Final selectfields is completely mapped!')
    
    new_df1=selectfields_tm1.toDF()
    #src_count=new_df1.count()
    #new_df1.printSchema()
    #new_df1.show()
    #print("Record count from source data: " +str(src_count))
    #new_df1.repartition(num_of_partitions)
    o_df = DynamicFrame.fromDF(new_df1, glueContext, "o_df")
    
    
    ## Match its catalog with target catalog table
    resolvechoice_tm = ResolveChoice.apply(frame = o_df, choice = "MATCH_CATALOG" \
                    , database = redshift_db, table_name = redshift_cata_tbl_nm 
                    , transformation_ctx = "resolvechoice_tm")

    resolvechoice_tm1 = ResolveChoice.apply(frame = resolvechoice_tm, choice = "make_cols" \
                    , transformation_ctx = "resolvechoice_tm1")

    print('resolve choice is completed')
    
    #PREACTIONS=PREACTIONS0.format(v_redshift_schema_name,mart_batch_id)
    #print(PREACTIONS)
    POSTACTIONS=POSTACTIONS0.format(v_redshift_schema_name,mart_batch_id,ods_batch_id \
        ,v_job_name,v_start_time,df_count)
    print(POSTACTIONS)


    ##DropNullFields
    dyf_dropNullfields = DropNullFields.apply(frame = resolvechoice_tm1)
    print("Null fields has been dropped!")

    
    ## load target table.
    datasink5 = glueContext.write_dynamic_frame.from_jdbc_conf(frame= dyf_dropNullfields, catalog_connection = rs_catalog_conn, connection_options ={"dbtable": rs_db_tbl, "database": rs_database}, redshift_tmp_dir = args["destinationbucket"], transformation_ctx = "datasink5")
    pg_insert(redshift_db_user,redshift_db_host,redshift_db_port, \
        redshift_db_name,redshift_db_pass,POSTACTIONS,cert_file_nm,conf_bucketname,region_name)
    
    pg_insert(redshift_db_user,redshift_db_host,redshift_db_port, \
        redshift_db_name,redshift_db_pass,dup_check,cert_file_nm,conf_bucketname,region_name)
    print("Job Completed")
    for item in os.listdir(os.getcwd()):
        os.remove(item)
    os.rmdir(work_dir)

except Exception as e:
    print(e)
    sys.exit(e)

job.commit()
