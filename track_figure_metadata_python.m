function track_figure_metadata_python(figPath, callerFile)
    % Dynamically locate the Python tracking script
    thisFilePath = mfilename('fullpath');
    [thisFolder, ~, ~] = fileparts(thisFilePath);
    pythonScript = fullfile(thisFolder, 'file_tracker.py');

    % Ensure the file has an extension
    [filepath, name, ext] = fileparts(figPath);
    if isempty(ext)
        figPath = fullfile(filepath, [name, '.png']); % Default to PNG if missing extension
    end
    
    fList = getAllDependencies(callerFile);
    fList_str = strjoin(fList, pathsep);

    disp(['Calling the python tracker: ', pythonScript])
    
    % Construct the system command
    cmd = sprintf('python "%s" "%s" "%s" --matlabdeps "%s"', pythonScript, figPath, callerFile, fList_str);
        
    [status, result] = system(cmd);

    % Display result
    if status == 0
        disp(['Figure metadata tracked for ', figPath]);
        disp(['Generated with the script ', callerFile]);
        disp(result);
    else
        disp('Error tracking metadata:');
        disp(result);
    end
end



function fList = getAllDependencies(callerFile)
    fprintf('Starting dependency analysis for: %s\n', callerFile);
    
    % Initialize list of dependencies
    [fList, ~] = matlab.codetools.requiredFilesAndProducts(callerFile);
    
    % Create a set to track visited files
    visitedFiles = containers.Map('KeyType', 'char', 'ValueType', 'logical');
    
    % Recursively collect dependencies
    fList = recursiveDependencySearch(fList, visitedFiles, 0);
    
    fList = unique(fList);
    
    fprintf('Dependency analysis complete. Total dependencies found: %d. They are:\n', numel(fList));
    disp(fList)
end

function fList = recursiveDependencySearch(fList, visitedFiles, depth)
    indent = repmat(' ', 1, depth * 4); % Indentation for readability

    % Iterate through each file in fList
    for i = 1:numel(fList)
        currentFile = fList{i};
        
        % Skip if already processed
        if isKey(visitedFiles, currentFile)
            fprintf('%s[SKIP] Already visited: %s\n', indent, currentFile);
            continue;
        end
        
        % Mark as visited
        visitedFiles(currentFile) = true;
        fprintf('%s[PROCESS] Checking dependencies of: %s\n', indent, currentFile);
        
        % Get dependencies of the current file
        [newDependencies, ~] = matlab.codetools.requiredFilesAndProducts(currentFile);
        
        % Append only new dependencies
        for j = 1:numel(newDependencies)
            if ~isKey(visitedFiles, newDependencies{j})
                fList{end+1} = newDependencies{j}; %#ok<AGROW>
                fprintf('%s  [FOUND] New dependency: %s\n', indent, newDependencies{j});
            else
                fprintf('%s  [SKIP] Already known: %s\n', indent, newDependencies{j});
            end
        end
        
        % Recursively process newly found dependencies
        if ~isempty(newDependencies)
            fprintf('%s[RECURSE] Exploring dependencies of: %s\n', indent, currentFile);
            fList = recursiveDependencySearch(fList, visitedFiles, depth + 1);
        end
    end
end
