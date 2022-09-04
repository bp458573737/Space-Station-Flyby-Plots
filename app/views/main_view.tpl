%# Slate theme imports:


% locations = content[1]
% spacecraft = content[2]


<!DOCTYPE html>
<!-- saved from url=(0029)https://bootswatch.com/slate/ -->
<html lang="en"><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">

    <title>Satellite Flybys</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="./Bootswatch_ Slate_files/bootstrap.css">
    <link rel="stylesheet" href="./Bootswatch_ Slate_files/font-awesome.min.css">
<!--    <link rel="stylesheet" href="./Bootswatch_ Slate_files/prism-okaidia.css">-->
    <link rel="stylesheet" href="./Bootswatch_ Slate_files/custom.min.css">

    </head>
<body>
    <div class="container">
      <div class="page-header" id="banner">
        <div class="row">
          <div class="col-lg-6">
            <h1>Satellite Flybys</h1>
            <p class="lead">Visualize a spacecraft's path through the sky near you</p>
          </div>
        </div>
      </div>

        <div class="row">
            <div class="col-md-4">
                <div class="bs-component" >
                    <form id='inputs' hx-post="/start" hx-target="#info" hx-swap="innerHTML">
                        <fieldset class="form-group px-1">
                            <legend class="mt-4">Configure Predicts</legend>
                            <div class="form-group">
                                <label for="locationSelect" class="form-label mt-4">Select viewing location</label>
                                <select class="form-select form-select-sm" id="locationSelect" name="location">
                                    % for loc in locations:
                                        % if loc == 'San Francisco':
                                            <option selected>{{loc}}</option>
                                        % else:
                                            <option>{{loc}}</option>
                                        % end
                                    % end
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="spacecraftSelect" class="form-label mt-4">Select spacecraft</label>
                                <select class="form-select form-select-sm" id="spacecraftSelect" name="spacecraft">
                                  % for sc in spacecraft:
                                    <option>{{sc}}</option>
                                    % end
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="durationSelect" class="form-label mt-4">How many day's worth of passes, starting from now?</label>
                                <select class="form-select form-select-sm" id="durationSelect" name="duration">
                                    <option>0.5</option>
                                    <option>1</option>
                                    <option>2</option>
                                    <option>4</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="min_elSelect" class="form-label mt-4">Low elevation cut-off (start/end passes at this value)</label>
                                <select class="form-select form-select-sm" id="min_elSelect" name="min_el">
                                    % for i in range(16):
                                        <option>{{i}}</option>
                                    % end
                                </select>
                            </div>
                            <button type="submit" class="btn btn-primary my-3">
                                Generate predicts</button>
                         </fieldset>
                    </form>
                </div>
            </div>
        </div>
        <hr>
        <div class="container-fluid overflow-auto" id="info">
            %# Below presents a sub-template
            % include(content[0], data=content[1:])
        </div>
    </div>


<!--    <script src="./Bootswatch_ Slate_files/jquery.min.js.download"></script>-->
    <script src="./Bootswatch_ Slate_files/bootstrap.bundle.min.js.download"></script>
<!--    <script src="./Bootswatch_ Slate_files/prism.js.download" data-manual=""></script>-->
    <script src="./Bootswatch_ Slate_files/custom.js.download"></script>
    <script src="https://unpkg.com/htmx.org@1.8.0"
    integrity="sha384-cZuAZ+ZbwkNRnrKi05G/fjBX+azI9DNOkNYysZ0I/X5ZFgsmMiBXgDZof30F5ofc"
    crossorigin="anonymous"></script>
</body>
</html>
