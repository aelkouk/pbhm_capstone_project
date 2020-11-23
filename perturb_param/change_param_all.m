function [] = change_param_all(row, sobolmatrix, soiltable_f)
    % load table to get input values
    params_sim = csvread(sobolmatrix,1,0);
    
    fprintf("-----------------")
    fprintf("-----------------\n")
    fprintf("New simulation \n")
    
    soil_tab_opt = "ROSETTA";
    auxi = strsplit(soiltable_f, '.');
    soil_table_or = fopen(strcat(auxi(1),"_or.",auxi(2)), 'r+');
    soil_table_new = fopen(soiltable_f, 'w+');
    % these are the option in the .csv file
    params_opt = ["theta_sat", "theta_res", "vGn_alpha", "vGn_n"];
    nparams = length(params_opt);
    
    % copy nlines up to ROSETTA opt
    i = 1;
    auxi = fgetl(soil_table_or);
    fprintf(soil_table_new,strcat(auxi,'\n'));
    while ~strcmp(string(auxi),soil_tab_opt)
        auxi = fgetl(soil_table_or);
        fprintf(soil_table_new,strcat(auxi,'\n'));
        i = i + 1;
    end
    
    % copy the first line after ROSETTA opt
    auxi = fgetl(soil_table_or);
    fprintf(soil_table_new,strcat(auxi,'\n'));
    % get info of params position from last stored line
    info_params = strsplit(strrep(auxi,"'", ' '), ' ');
    
    % modify all the rows in the column of param_to_mod
    for i = 1:12
        auxi = fgetl(soil_table_or);
        old_str = string(strsplit(auxi, " "));
        for ii = 1:nparams
            id = info_params == params_opt(ii);
            old_str(id) = string(double(params_sim(row,params_opt(ii) ...
                ==params_opt)));
        end
        if i < 10
            auxinew = sprintf('%1.0f %13.3f %11.3f %11.3f %11.3f', ...
                double(old_str(1:5)));
        else
            auxinew = sprintf('%1.0f %12.3f %11.3f %11.3f %11.3f', ...
                double(old_str(1:5)));
        end
        fprintf(soil_table_new,strcat(auxinew,auxi(52:end),'\n'));
    end
    
    % close fileID
    fclose(soil_table_or);
    fclose(soil_table_new);
    
    % print info
    fprintf("SOILPARM.TBl created \n")
end
