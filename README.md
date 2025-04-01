# DGCRN-TSA
Dynamic Graph Convolutional Recurrent Network with Temporal Self-Attention for Accurate Traffic Flow Prediction
<img align="right" src="https://github-readme-stats.vercel.app/api?username=lixin8383&show_icons=true&icon_color=CE1D2D&text_color=718096&bg_color=ffffff&hide_title=true" />


# Introduction to DGCRN-TSA
Precision in traffic flow prediction represents a pivotal technology within the domain of Intelligent Transportation Systems (ITS), playing a critical role in the planning of future trips, the enhancement of urban transportation efficiency, and the support of decision-making processes by traffic management authorities. Current mainstream graph-convolutional networks predominantly depend on a priori knowledge to depict the spatial dependencies of road networks in the context of predefined adjacency matrices. However, the predefined or adaptive adjacency matrices employed for such static modeling of spatial dependencies are challenging to accurately reflect the dynamically changing spatial associations between road segments over time, thus limiting the precise prediction of traffic flow. To address this challenge, a Dynamic Graph Convolutional Recurrent Network and Temporal Self-Attention (DGCRN-TSA) is proposed for traffic flow prediction. The proposed method integrates a dynamic graph convolutional recurrent network with a recurrent neural network-based dynamic graph generation model to construct a dynamic graph from time-varying traffic signals, facilitating the simultaneous extraction of spatial and temporal features. Additionally, the model separates abnormal signals from normal traffic signals and employs a data-driven approach to model abnormal signals, thereby further enhancing the prediction efficacy. The model incorporates a novel temporal attention mechanism, which utilizes local contextual information to enhance the transformation of numerical sequence representations. This mechanism enables the prediction model to capture dynamic temporal dependencies in traffic flows, thereby contributing to long-term prediction. An analysis of four real datasets revealed that DGCRN-TSA outperforms current state-of-the-art prediction methods in terms of performance.

# PeMS-Datasets
This repository houses all objects associated with the storage, loading, and summarization of data-sets from the Caltrans Performance Measurement System (PeMS).https://github.com/SANDAG/PeMS-Datasets

## PeMS data-sets location and acquisition
PeMS data-sets come from the PeMS Data Clearinghouse located at http://pems.dot.ca.gov/. To access the PeMS Data Clearinghouse it is necessary to create a user-name and password.

To download the data-sets it is recommended to use a batch downloader browser extension as Caltrans purposefully disallows the use of programmatic tools to access the data-sets. Once the data-sets of interest are downloaded ensure there are no duplicate files or empty files as this is not an uncommon occurrence in the Data Clearinghouse.

## Loading PeMS data-sets
The final destination of the PeMS data-sets is an internal SQL server instance specified in the Python file main.py of the project python folder. 

Once the data-sets are downloaded, placed in the project data folder, and ready to be loaded into the SQL server instance; ensure the PeMS SQL objects created by the pemsObjects.sql file in the project sql folder exist in the target database of interest. If they do not exist, or it is wished to completely start anew, run the pemsObjects.sql in the target database of interest to drop and create all PeMS related SQL objects.

Create the Python interpreter from the provided environment.yml file located in the Python folder of the project. Set the interpreter as the default Python interpreter associated with this project. Run the Python file main.py from the project python folder. It will sequentially load the  data-sets of interest from the data folder, extracting the necessary txt files from the compressed gz files and zip archives, and load them directly into the SQL database of interest specified in the Python file main.py.

## Summarizing PeMS data-sets
Stored procedures within the database containing the PeMS data-sets provide yearly aggregations of the PeMS data-sets at the station level for user-specified time resolutions. For more information, refer to this GitHub's Wiki page for each PeMS data-set.

## Matching PeMS stations to SANDAG highway network
A Python micro-service is included in the project matching folder that matches a user-specified year of PeMS station metadata loaded into an internal SQL server instance with a user-specified SANDAG highway network e00 file. The Python script can be run outside of the project folder structure and includes a separate environment.yml file from the main project.

## Acquisition of support
This work was supported in part by the 2025 Gansu Provincial Department of Education Excellent Graduate Students “Innovation Star” Program(2025CXZX-645); National Natural Science Foundation of China Western Program (72361017; 52362047; 71861024); Gansu Provincial Key R&D Program (21YF5GA052); Gansu Provincial Natural Science Foundation Program (18JR3RA119); Gansu Higher Education Institutions Industrial Support Program in 2021 (2021CYZC-60); Gansu Provincial Department of Education Key Project of “Double First-class” Scientific Research (GSSYLXM-04); Natural Science Foundation of Gansu (23JRRA904).
