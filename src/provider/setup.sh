#ディレクトリ作成
mkdir -p catalog-search/swagger_server/utilities
mkdir -p connector-main/swagger_server/utilities
mkdir -p data-exchange/swagger_server/utilities
mkdir -p authorization/swagger_server/utilities
mkdir -p provenance-management/swagger_server/utilities

array=`find ../common/swagger_server/utilities  -type f`
for e in $array; do
    ln -f ${e} catalog-search/swagger_server/utilities/`basename ${e}`
    ln -f ${e} connector-main/swagger_server/utilities/`basename ${e}`
    ln -f ${e} data-exchange/swagger_server/utilities/`basename ${e}`  
    ln -f ${e} authorization/swagger_server/utilities/`basename ${e}`
    ln -f ${e} provenance-management/swagger_server/utilities/`basename ${e}`
done
                                                                                               
ln -f ../common/swagger_server/services/provide_data_ftp.py   connector-main/swagger_server/services/provide_data_ftp.py  
ln -f ../common/swagger_server/services/provide_data_http.py  connector-main/swagger_server/services/provide_data_http.py 
ln -f ../common/swagger_server/services/provide_data_ngsi.py  connector-main/swagger_server/services/provide_data_ngsi.py 
ln -f ../common/swagger_server/services/ckan_access.py        connector-main/swagger_server/services/ckan_access.py       

