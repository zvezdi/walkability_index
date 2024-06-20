import folium

import geopandas as gpd
from shapely.geometry import Point, MultiLineString, Polygon
from helpers import crs_transform_coords, crs_transform_polygon
import pandas as pd
import os
from dotenv import load_dotenv

from database import db_engine, gdf_from_sql, create_table_form_dgf
from queries import pedestrian_network_query, administrative_regions_query, residential_buildings_query, poi_parks_query, poi_schools_query, poi_query
from network import build_network_from_geodataframe, find_nearest_node, shortest_path, compute_accessibility_isochron
from helpers import crs_transform_coords
import networkx as nx


# Load environment variables from a .env file
load_dotenv()
database = db_engine(os.getenv('DB_CONNECTION_STRING'))

SCOPE = 'Lozenec'
SCHEMA = 'zvezdi_work'

with database.connect() as db_connection:
  gdf_pedestrian_network = gdf_from_sql(db_connection, pedestrian_network_query(SCOPE))
  gdf_adm_regions = gdf_from_sql(db_connection, administrative_regions_query())
  gdf_residential_buildings_lozenec = gdf_from_sql(db_connection, residential_buildings_query(SCOPE))

pedestrian_network = build_network_from_geodataframe(gdf_pedestrian_network, swap_xy = False, save_as = "lib/saves/pedestrian_network.graph")

points = [
 [321540.0290951831, 4730158.139271268],
[320440.8561229653, 4725003.558597337],
[322861.7086831326, 4724738.602608356],
[322863.1859403249, 4724731.719090797],
[322868.613074451, 4724722.64889819],
[320214.1127607809, 4724927.958534905],
[322667.7197327416, 4724734.084006023],
[322662.9207356069, 4724746.406392601],
[320085.9443293629, 4725270.587584459],
[320618.8380602775, 4725475.587401887],
[322982.1696047433, 4726689.467011913],
[322916.5951156832, 4726731.835258189],
[320471.0981305981, 4724694.799967632],
[322014.3280648942, 4727849.474148751],
[322014.3280648942, 4727849.474148751],
[320744.359113538, 4724942.827810604],
[320757.26852790883, 4724859.05574501],
[320757.26852790883, 4724859.05574501],
[320757.26852790883, 4724859.05574501],
[320404.47119193745, 4726727.546854167],
[320433.42770795326, 4724994.732252948],
[321775.0528925315, 4730623.074313385],
[321540.0290951831, 4730158.139271268],
[322176.0118334848, 4729966.589349963],
[322042.7029659146, 4729956.602099557],
[322029.9258888395, 4729957.808121384],
[322001.48605920566, 4729959.918606416],
[321987.2292725282, 4729955.998853271],
[321979.2382755108, 4729953.594918104],
[321963.146210292, 4729949.3914854815],
[322023.15450740745, 4729953.353044447],
[322015.13734005427, 4729953.88586396],
[321974.8869372426, 4729947.382278046],
[322000.0978248896, 4729912.831749666],
[321625.92772112944, 4729169.852456536],
[321640.18509310565, 4729167.763239899],
[321640.18509310565, 4729167.763239899],
[322025.30514199124, 4729911.894153549],
[322221.62172193103, 4729685.648288744],
[321317.7259923937, 4727172.908452018],
[321317.7259923937, 4727172.908452018],
[322212.5259316795, 4729751.2623277055],
[322182.3360780915, 4729748.33665011],
[322315.3787196248, 4728978.021154849],
[322315.3787196248, 4728978.021154849],
[322296.6603421159, 4728969.5835485235],
[322245.26733757125, 4728946.136897835],
[322245.26733757125, 4728946.136897835],
[322233.5258843294, 4728940.38486658],
[322224.11466320907, 4728936.14399995],
[321999.86388447875, 4729016.548708009],
[320911.6238736514, 4728084.697865551],
[320910.0102829381, 4728082.354921307],
[320904.34710855177, 4728049.630137839],
[320904.34710855177, 4728049.630137839],
[320904.34710855177, 4728049.630137839],
[320904.34710855177, 4728049.630137839],
[320917.4148053343, 4728084.697949105],
[320925.34153990063, 4728630.404568096],
[320911.43126197066, 4728616.258657378],
[320911.43126197066, 4728616.258657378],
[320958.38569927635, 4728529.51905488],
[321040.6025260312, 4728566.3605666],
[320925.34153990063, 4728630.404568096],
[320911.43126197066, 4728616.258657378],
[321046.84213291976, 4728569.197946451],
[321369.7437027608, 4728907.08308244],
[321325.94353423256, 4728889.479171308],
[321404.7122828921, 4728731.5396714],
[321442.8835279971, 4728914.994514995],
[321608.48793965275, 4726368.112827795],
[321910.08627888217, 4725034.319478209],
[321893.3206906171, 4725024.0119363805],
[321690.6723168676, 4724631.067451733],
[321624.6784941667, 4726392.251729272],
[322473.1521011388, 4726677.508077654],
[321848.05307419365, 4726637.038104484],
[322364.926672296, 4724548.385089249],
[321378.3402122176, 4724813.5800029775],
[321608.48793965275, 4726368.112827795],
[322502.25570347207, 4726616.35027906],
[322008.0953780012, 4725131.437460299],
[322008.0953780012, 4725131.437460299],
[321910.08627888217, 4725034.319478209],
[321156.89368330326, 4725071.838027831],
[321861.1707150169, 4726618.357507451],
[321861.1707150169, 4726618.357507451],
[321690.6723168676, 4724631.067451733],
[321699.8538711308, 4724576.328493716],
[321870.5940964931, 4725003.893073679],
[321870.5940964931, 4725003.893073679],
[321870.5940964931, 4725003.893073679],
[321575.0488672415, 4727571.675310267],
[322879.2010842193, 4724627.661351177],
[322001.522578949, 4727878.396695138],
[321979.0030289988, 4727926.968519844],
[322384.42110007897, 4725550.189655634],
[320933.55388292694, 4728638.8922088295],
[320673.40339251247, 4725707.420845542],
[321924.0640953681, 4725617.40053516],
[320194.9492956338, 4725180.000761998],
[320477.9216951544, 4724696.554745316],
[322133.1341094513, 4723582.556793964],
[321723.6168735648, 4729975.270922899],
[322133.1341094513, 4723582.556793964],
[322133.1341094513, 4723582.556793964],
[321870.5940964931, 4725003.893073679],
[321870.5940964931, 4725003.893073679],
[321723.8980781293, 4730491.156817098],
[321382.9464601273, 4728908.550140689],
[320214.1127607809, 4724927.958534905],
[321705.5879149237, 4730052.774696089],
[320695.37148401636, 4725706.131054453],
[320491.61012124154, 4724748.192681662],
[322962.2251906075, 4726778.997848912],
[320689.8718933747, 4725705.15763991],
[320943.50688654813, 4726603.960910938],
[320684.28930441395, 4725705.047189346],
[320397.34728020994, 4725130.459961871],
[320688.87302870536, 4728419.602660578],
[321699.8538711308, 4724576.328493716],
[322822.37252326874, 4723873.100058649],
[322764.84889631683, 4723892.389897463],
[320397.42546804866, 4726669.704679815],
[321476.34826048143, 4725423.318761334],
[322769.8430611425, 4726294.748024668],
[320907.33407116815, 4724821.936418007],
[321248.22633840144, 4724890.117705368],
[320907.33407116815, 4724821.936418007],
[320907.33407116815, 4724821.936418007],
[321248.22633840144, 4724890.117705368],
[320907.33407116815, 4724821.936418007],
[320907.33407116815, 4724821.936418007],
[320907.33407116815, 4724821.936418007],
[321248.22633840144, 4724890.117705368],
[321248.22633840144, 4724890.117705368],
[321248.22633840144, 4724890.117705368],
[320183.4276888208, 4725518.65181448],
[320183.4276888208, 4725518.65181448],
[320404.47119193745, 4726727.546854167],
[320203.8710904707, 4725641.225388339],
[320203.8710904707, 4725641.225388339],
[320404.47119193745, 4726727.546854167],
[320666.2693038618, 4725713.590139798],
[320526.8814752492, 4728488.989920863],
[320277.50793378404, 4725562.579609531],
[320397.42546804866, 4726669.704679815],
[320398.934474005, 4726696.070687429],
[320362.53448784235, 4725520.111909142],
[320386.0063724868, 4725512.161570328],
[320479.77508089214, 4725669.1667233305],
[320511.22169435356, 4725750.1146024605],
[320511.22169435356, 4725750.1146024605],
[322597.7603296756, 4723800.562105609],
[322388.1068617195, 4725575.973500006],
[322869.11889738264, 4726583.429331027],
[322682.4517198021, 4726564.427516216],
[323036.6137094923, 4726722.682130248],
[322829.69468924135, 4724658.818877857],
[322622.1469251166, 4726505.011239689],
[323019.8267397167, 4726711.632948778],
[322948.29638045357, 4726657.093363257],
[322880.25132565526, 4726593.940229068],
[322897.3072950409, 4726611.437755317],
[322660.4315175109, 4725785.36340224],
[323004.6385348176, 4726703.010826698],
[322769.8430611425, 4726294.748024668],
[322676.0224608682, 4726332.196987707],
[322906.91231210355, 4726622.125294214],
[321747.9672878762, 4730487.520113224],
[322676.4752708714, 4726551.715353825],
[322676.4752708714, 4726551.715353825],
[321494.4896674043, 4730198.060944245],
[321743.510975476, 4730625.218098487],
[322744.7671822351, 4726947.719434085],
[322776.9405343801, 4726947.084441091],
[322808.2672629452, 4726948.989556422],
[322776.9405343801, 4726947.084441091],
[322776.9405343801, 4726947.084441091],
[322776.9405343801, 4726947.084441091],
[321770.4033941033, 4730041.117737744],
[321723.8980781293, 4730491.156817098],
[321695.80409136927, 4730495.310915129],
[321721.5201295493, 4730491.503378885],
[321499.27392673225, 4730227.5117205465],
[321747.9672878762, 4730487.520113224],
[322176.27612512547, 4730556.724313313],
[321543.5079121349, 4730090.562991346],
[321734.27349003055, 4729979.665930215],
[321744.60673999327, 4730488.029298071],
[321503.8286846194, 4730254.29329699],
[321744.99727138167, 4729984.062447276],
[321502.5420879364, 4730247.038689742],
[321747.9672878762, 4730487.520113224],
[321506.813634938, 4730272.851524573],
[321747.2134025158, 4730054.227657066],
[321716.1030879065, 4730050.892598437],
[321737.39839310513, 4729980.954667286],
[321711.5070969198, 4729970.210531876],
[321724.2175344301, 4730049.452441826],
[321783.42773367604, 4730038.759598014],
[322176.27612512547, 4730556.724313313],
[321543.5079121349, 4730090.562991346],
[321747.9672878762, 4730487.520113224],
[321740.05693555815, 4730488.723103452],
[321752.84033617756, 4730053.230685507],
[321497.0489180201, 4730212.988644704],
[321759.95456694183, 4729990.182549221],
[321505.63133040647, 4730265.683343784],
[321735.94412920903, 4730489.353327321],
[321724.2175344301, 4730049.452441826],
[321755.980066649, 4730043.617356351],
[321766.0933868883, 4730050.879737722],
[321711.78917309304, 4730492.960834976],
[321732.7742705982, 4730056.889072009],
[320477.9216951544, 4724696.554745316],
[320822.2947139551, 4724726.267300446],
[320694.7245235844, 4724969.091797777],
[322529.7697330711, 4723800.439737024],
[320751.84312762355, 4724861.30935928],
[320109.3780850619, 4725245.447385147],
[320502.71113291767, 4725083.636571303],
[320109.3780850619, 4725245.447385147],
[320194.9492956338, 4725180.000761998],
[320040.1816700027, 4725285.395852237],
[320751.84312762355, 4724861.30935928],
[320192.96831436455, 4724873.316052971],
[320194.9492956338, 4725180.000761998],
[320192.96831436455, 4724873.316052971],
[320419.5303855287, 4724929.315724254],
[320533.5657373814, 4724855.585737602],
[320324.86233435036, 4724932.002390471],
[320195.3113414198, 4724978.217950659],
[320192.96831436455, 4724873.316052971],
[320189.4069920252, 4725005.192438632],
[322703.2119266117, 4723787.688439931],
[320533.5657373814, 4724855.585737602],
[320084.58146582753, 4725264.440708913],
[322703.2119266117, 4723787.688439931],
[320822.2947139551, 4724726.267300446],
[320751.84312762355, 4724861.30935928],
[322597.7603296756, 4723800.562105609],
[322688.1345171147, 4723923.105408133],
[320694.7245235844, 4724969.091797777],
[320332.82739877497, 4724930.293069476],
[322719.3486727007, 4723837.100416258],
[320157.3122681855, 4725218.06883332],
[320214.1127607809, 4724927.958534905],
[320443.4040944874, 4725052.290296877],
[320331.14218045527, 4725092.103561296],
[320509.7500998246, 4724793.709459708],
[320433.42770795326, 4724994.732252948],
[320533.5657373814, 4724855.585737602],
[320189.4069920252, 4725005.192438632],
[320371.30527865945, 4724923.031463975],
[322719.3486727007, 4723837.100416258],
[322764.84889631683, 4723892.389897463],
[320480.92647449253, 4724714.0270468425],
[320751.84312762355, 4724861.30935928],
[320655.1059001135, 4724994.24304069],
[320694.7245235844, 4724969.091797777],
[320751.84312762355, 4724861.30935928],
[320432.73910253297, 4724959.300801935],
[320175.0507701979, 4724955.669222115],
[320109.3780850619, 4725245.447385147],
[320751.84312762355, 4724861.30935928],
[320157.3122681855, 4725218.06883332],
[322688.1345171147, 4723923.105408133],
[320371.30527865945, 4724923.031463975],
[320342.2432940988, 4725082.588416257],
[320425.41493982094, 4724927.437631096],
[320694.7245235844, 4724969.091797777],
[320744.359113538, 4724942.827810604],
[320214.1127607809, 4724927.958534905],
[320202.6502716617, 4724984.492821689],
[322703.2119266117, 4723787.688439931],
[320751.84312762355, 4724861.30935928],
[320533.5657373814, 4724855.585737602],
[322688.1345171147, 4723923.105408133],
[320371.30527865945, 4724923.031463975],
[320500.7191944992, 4725041.695170402],
[320175.0507701979, 4724955.669222115],
[320428.10670668946, 4724965.06004614],
[320157.3122681855, 4725218.06883332],
[322692.5283059112, 4723833.761827079],
[322688.1345171147, 4723923.105408133],
[320172.7138727951, 4724958.896539247],
[322764.84889631683, 4723892.389897463],
[320331.14218045527, 4725092.103561296],
[322703.2119266117, 4723787.688439931],
[320157.3122681855, 4725218.06883332],
[320433.42770795326, 4724994.732252948],
[322597.7603296756, 4723800.562105609],
[320071.5462887207, 4725278.162114104],
[320157.3122681855, 4725218.06883332],
[320425.41493982094, 4724927.437631096],
[320407.93110212905, 4725077.2465848625],
[320342.2432940988, 4725082.588416257],
[320468.4273080961, 4724682.1133176815],
[320175.0507701979, 4724955.669222115],
[320109.3780850619, 4725245.447385147],
[320109.3780850619, 4725245.447385147],
[320402.9859098018, 4725134.911581211],
[320504.30276612623, 4725115.25660058],
[320509.7500998246, 4724793.709459708],
[320084.58146582753, 4725264.440708913],
[322703.2119266117, 4723787.688439931],
[320404.47119193745, 4726727.546854167],
[320404.47119193745, 4726727.546854167],
[322328.73618511483, 4728984.296115122],
[321500.1749972702, 4727532.974925384],
[320397.42546804866, 4726669.704679815],
[322663.5688800075, 4726546.280567233],
[322662.1904713142, 4726544.860573009],
[321695.80409136927, 4730495.310915129],
[321732.7742705982, 4730056.889072009],
[320668.37907028466, 4725709.851619172],
[322703.2119266117, 4723787.688439931],
[320192.96831436455, 4724873.316052971],
[320369.30196801, 4724917.355935249],
[322529.7697330711, 4723800.439737024],
[322688.1345171147, 4723923.105408133],
[322658.1608709813, 4723937.943824345],
[322512.23151214106, 4726769.708075183],
[322473.1521011388, 4726677.508077654],
[320398.4272192869, 4726653.439469696],
[322609.98317183077, 4723824.002237131],
[322658.1608709813, 4723937.943824345],
[320395.24433465, 4725076.4119658],
[320332.82739877497, 4724930.293069476],
[322719.3486727007, 4723837.100416258],
[322658.1608709813, 4723937.943824345],
[322658.1608709813, 4723937.943824345],
[320308.6221813374, 4724933.047447317],
[322597.7603296756, 4723800.562105609],
[320404.47119193745, 4726727.546854167],
[320404.47119193745, 4726727.546854167],
[323317.1639234114, 4727892.586610753],
[320565.28292105, 4724981.007232659],
[322829.0156672517, 4726539.966463779],
[322666.7396766438, 4726361.090614951],
[322674.18806337315, 4725803.827106521],
[320491.61012124154, 4724748.192681662],
[321932.6502615552, 4728811.023867564],
[320491.61012124154, 4724748.192681662],
[320509.7500998246, 4724793.709459708],
[321948.6640976474, 4725658.548588708],
[322676.0224608682, 4726332.196987707],
[322718.2708653335, 4725900.218192314],
[320789.70887217147, 4724927.970745753],
[320975.84739672416, 4724403.965881901],
[320477.9216951544, 4724696.554745316],
[320194.9492956338, 4725180.000761998],
[320224.663288314, 4725156.045987375],
[320511.22169435356, 4725750.1146024605],
[320509.7500998246, 4724793.709459708],
[321513.44768719876, 4727541.357656991],
[320533.5657373814, 4724855.585737602],
[322722.1051090461, 4725926.565968172],
[322690.84509812575, 4726598.750904222],
[322597.7603296756, 4723800.562105609],
[322692.5283059112, 4723833.761827079],
[322529.7697330711, 4723800.439737024],
[322609.98317183077, 4723824.002237131],
[322241.75125995744, 4723670.400172123],
[322241.75125995744, 4723670.400172123],
[320533.5657373814, 4724855.585737602],
[322688.49650546606, 4726589.128452205],
[321747.0325918478, 4730045.355261089],
[322609.98317183077, 4723824.002237131],
[322605.4762953059, 4723820.940254538],
[322692.5283059112, 4723833.761827079],
[320432.73910253297, 4724959.300801935],
[322529.7697330711, 4723800.439737024],
[322597.7603296756, 4723800.562105609],
[322609.98317183077, 4723824.002237131],
[320519.9256794834, 4724836.191617235],
[322719.3486727007, 4723837.100416258],
[320404.47119193745, 4726727.546854167],
[320157.3122681855, 4725218.06883332],
[320172.7138727951, 4724958.896539247],
[321501.92712970136, 4727553.803058652],
[321406.99977442285, 4727109.14540486],
[322764.84889631683, 4723892.389897463],
[320398.934474005, 4726696.070687429],
[320192.96831436455, 4724873.316052971],
[322645.90452270454, 4723710.513208125],
[320333.13587249076, 4725085.563505868],
[320480.92647449253, 4724714.0270468425],
[320172.7138727951, 4724958.896539247],
[322645.90452270454, 4723710.513208125],
[322692.5283059112, 4723833.761827079],
[320397.42442061845, 4725076.463807787],
[320172.7138727951, 4724958.896539247],
[320433.42770795326, 4724994.732252948],
[320395.24433465, 4725076.4119658],
[320342.2432940988, 4725082.588416257],
[320945.4483263942, 4726575.812832239],
[320398.934474005, 4726696.070687429],
[321625.26729553175, 4726470.555511768],
[320400.0716744289, 4726637.813407117],
[322662.1904713142, 4726544.860573009],
[322662.1904713142, 4726544.860573009],
[320192.96831436455, 4724873.316052971],
[322529.7697330711, 4723800.439737024],
[322645.90452270454, 4723710.513208125],
[320448.59760870266, 4725049.638758991],
[320452.8335162202, 4725052.073455715],
[320441.51821620803, 4725055.953854553],
[320502.71113291767, 4725083.636571303],
[321981.5609177784, 4729949.124475702],
[322676.4752708714, 4726551.715353825],
[320402.9859098018, 4725134.911581211],
[320480.92647449253, 4724714.0270468425]
]


df = pd.DataFrame(points, columns=['x', 'y'])

center_lon, center_lat = crs_transform_coords(df.x.mean(), df.y.mean())

m = folium.Map(location=[center_lat, center_lon], zoom_start=14)

# Add edges to the map
for start_node, end_node in pedestrian_network.edges:
  start_lon, start_lat = crs_transform_coords(start_node[0], start_node[1])
  end_lon, end_lat = crs_transform_coords(end_node[0], end_node[1])
  folium.PolyLine(
    locations=[[start_lat, start_lon], [end_lat, end_lon]],
    color='#62635b'
  ).add_to(m)

# Add nodes to the map
for node in pedestrian_network.nodes:
  lon, lat = crs_transform_coords(node[0], node[1])
  folium.CircleMarker(
    location=[lat, lon],
    radius=5,
    color='#a6b86c',
    fill=True,
    fill_color='#a6b86c',
    fill_opacity=0.5,
    popup=f'Node {node}'
  ).add_to(m)

for idx, row in df.iterrows():
  lon, lat = crs_transform_coords(row.x, row.y)
  marker = folium.CircleMarker(
    location=[lat, lon],
    radius=7,
    color='red',
    fill=True,
    fill_color='#426e0e',
    fill_opacity=1,
  )
  marker.add_to(m)


m.save('lib/saves/residentials_without_polygons.html')
m
