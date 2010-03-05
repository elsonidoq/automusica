<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html lang="en">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <title>Raphaël · Interactive Chart</title>
        <link href="/css/comparision_experiment.css" rel="stylesheet" type="text/css" media="screen">

        <script src="/js/raphael.js" type="text/javascript" charset="utf-8"></script>
        <script src="/js/jquery.js" type="text/javascript" charset="utf-8"></script>
        <script src="/js/player.js" type="text/javascript"></script>
        <script src="/js/jquery.jplayer.js" type="text/javascript"></script>
        <script src="/js/hsv2rgb.js" type="text/javascript" charset="utf-8"></script>
        <script src="/js/spinner.js" type="text/javascript" charset="utf-8"></script>
        

        <script type="text/javascript" charset="utf-8">
            var buttons= null;
            var selector= null;
            var on_mouse_down= false;
            var selected_button= null;
            var r;
            var is_test_sound = false;
            var play1_playlist= ${playlist1};
            var play2_playlist= ${playlist2};
            var nplayed= ${nplayed};
            var caching= false;
            var spinner= null;
            var ntraining= ${ntraining};

            function find_closest_button(x) {
                var last_distance=null, actual_distance= null;
                for (var i=0; i<buttons.length; i++) {
                    actual_distance= Math.abs(x - buttons[i].attrs.cx);
                    if (last_distance && last_distance < actual_distance) {
                        return [buttons[i-1], last_distance];
                    }
                    last_distance= actual_distance;
                }
                return [buttons[buttons.length-1], last_distance]
            }

            function start_experiment() {
                if (is_test_sound) {
                    var jplayer= $("#jplayer");
                    jplayer.stop();
                    is_test_sound= false;
                }
                $("#description").slideUp(500, function() {
/*                    status.show_status('Click para escuchar');*/
                    $("#experiment-wrapper").fadeIn();
                });
/*                $("#experiment_progress").fadeIn(500);
                if (${ntraining} > 0) {
                   experiment_progress_text.show_status('Practicando');
                } else {
                   experiment_progress_text.show_status('Experimentando');
                }*/
            }
            
                
            $(window).mouseup(function(e) {
                if (on_mouse_down) {
                    on_mouse_down= false;
                    $("#holder").unbind('mousemove');
                    var button, distance;
                    var l= find_closest_button(e.clientX - $("#holder").position().left);
                    var button= l[0], distance= l[1];
                    selector.animate({cx:button.attrs.cx}, 100, change_selected_button(button));
                }
            });
            function change_selected_button(button) {
                var f= function() {
                    button.node.style.cursor = "move";
                    selected_button.node.style.cursor = "";
                    selected_button= button;
                }
                return f
            }
            function mousedown_handler(e){
                var l= find_closest_button(e.clientX - $("#holder").position().left);
                var button= l[0], distance= l[1];
                selected_button.node.style.cursor = "";
                if (distance < 20) {
                    if (selector.attrs.cx == button.attrs.cx) {
                        var h= $("#holder");
                        on_mouse_down= true;
                        h.mousemove(function(e) {
                            selector.animate({cx:e.clientX - h.position().left}, 100);
                        });
                    } else {
                        selector.animate({cx:button.attrs.cx}, 300, change_selected_button(button));
                    }
                } else {
                    selector.animate({cx:button.attrs.cx}, 300, change_selected_button(button));
                }
            } 
            $(document).ready(function() {
               var jplayer= $("#jplayer").jPlayer({
                    ready: function () {



                    }
                    ,swfPath:'/js'
                })
               .onProgressChange( function(lp,ppr,ppa,pt,tt) {
                    if (caching && lp < 100) {
                        var lp= parseInt(lp);
                        if (lp % 10 == 0)  {
                            $("#loader_bar").animate({"width":lp+"%"});
                        }
                    } else if(caching && lp >= 100) {
                        $(".loader").fadeOut();
                        caching= false;
                        jplayer.volume(100);
                        jplayer.playHead(0);
                        
                        status.hide_status();
                        $("#loader_bar").fadeOut(500, function() {
                            $('#playing_img').fadeIn();
                        });
                    } 
                        
                }).onSoundComplete( function() {
                    if (is_test_sound) {
                        is_test_sound= false;
                    } else {
                        $(".play_hablando").hide();
                        $(".play_callado").show();
                    }

                    
                });
            });

            window.onload = function () {
                spinner= new Spinner("experiment_progress", 10, 40, play1_playlist.length, 2, "#fff", "#abb1f0", ntraining, "#fff", "#cfabf0");
            
                resize();
                var W = 640,
                    H = 50,
                    values = [],
                    len = 9;
                for (var i = len; i--;) {
                    values.push(50);
                }
                r = Raphael("holder", W, H);
                r.safari();
                
                function translate(x, y) {
                    return [
                        10 + (W-20) / (values.length - 1) * x,
                        H - 10 - (H - 20) / 100 * y
                    ];
                }
                buttons = r.set();
                var h=229/360, v=0.83, s=0.4;
                var s0= 0, s1= 0.81;
                var v0= 0.53, v1= 0.84;

                for (var i = 0, ii = values.length - 1; i < ii; i++) {
                    var xy = translate(i, values[i]),
                        xy1 = translate(i + 1, values[i + 1]),
                        f;

                    var line_s, line_v;
                    if (i < 4) {
                        line_v= (v1 - v0)/(ii-4)*Math.abs(i-4) + v0;
                        line_s= (s1 - s0)/(ii-4)*Math.abs(i-4) + s0;
                    } else {
                        line_s= (s1 - s0)/(ii-4)*Math.abs(i-3) + s0;
                        line_v= (v1 - v0)/(ii-4)*Math.abs(i-3) + v0;
                    }
                    var line_color= 'hsb(' + h + ',' + line_s + ',' + line_v + ')';

                    var l= [['M', xy[0], xy[1]]]
                    l.push(["L", xy1[0], xy1[1]]); 
                    r.path(l.join(',')).attr({stroke: line_color, "stroke-width": 2});

                    (f = function (i, xy) {
                        s= (s1 - s0)/(ii-4)*Math.abs(i-4) + s0;
                        v= (v1 - v0)/(ii-4)*Math.abs(i-4) + v0;
                        var color= 'hsb(' + h + ',' + s + ',' + v + ')';
                        buttons.push(r.circle(xy[0], xy[1], 7).attr({fill: color, stroke: "none"}));
                    })(i, xy);
                    if (i == ii - 1) {
                        f(i + 1, xy1);
                    }
                }
                //path.attr({path: p.join(",")});
                var rectangle= r.rect(0, 0, W, H).attr({stroke:"none", fill:"#fff", opacity:0}).mousedown(mousedown_handler);
                var selector_xy= translate(4, values[4]);
                selector= r.circle(selector_xy[0], selector_xy[1], 9)
                $("#holder").mousedown(mousedown_handler);
                buttons.mousedown(mousedown_handler);
                selector.node.style.cursor = "move";
                buttons[4].node.style.cursor = "move";
                selected_button= buttons[4];
            };
        </script>
    </head>
    <body>
        <div id="description">
        <div id="description_container" >
            ${experiment_description}
        </div>
        <div id="comenzar">
            <a id="a_comenzar" href="#" onclick="javascript:start_experiment();">comenzar</a>
        </div>
        </div>

        <div id="jplayer"></div>

        <div style="align:right;width:100%">
            <div style="text-align:right;" id="experiment_progress" > 
                <div style="display:none;" id="experiment_progress_text"></div>
            </div>
        </div>
        <div id="experiment-wrapper" >
            <div id="holder" style="display:inline;"> </div>
            <div id="play1" style="display:inline;float:left;margin-top:-58px;margin-left:-80px;height:60px;width:60px;">
                <img class="play_callado" id="play1_callado" style="height:100%;width:100%" 
                     src="/images/speaker_callado.png" onclick="javascript:play(this)"/> 
                <img class="play_hablando" id="play1_hablando" style="display:none;height:100%;width:100%" 
                     src="/images/speaker_hablando.png" onclick="javascript:stop(this)"/> 
                <div class="loader" id="play1_loader" style="display:none;text-align:center;"> <img src="/images/loader.gif"/> </div>
            </div>
            <div id="play2" style="margin-top:-58px;margin-right:-80px;float:right;height:60px;width:60px;">
                <img class="play_callado" id="play2_callado" 
                     style="height:100%;width:100%" src="/images/speaker_callado.png" onclick="javascript:play(this)"/> 
                <img class="play_hablando" id="play2_hablando" 
                     style="display:none;height:100%;width:100%" src="/images/speaker_hablando.png" onclick="javascript:stop(this)"/> 
                <div class="loader" id="play2_loader" style="display:none;text-align:center;"> <img src="/images/loader.gif"/> </div>
            </div>
            <div style="text-align:center">
            <a href="#" onclick="javascript:next()">Pr&oacute;ximo</a>
            </div>
        </div>
    <script type="text/javascript">
    function next() {
        var h= $("#experiment-wrapper");
        var ww= $(window).width();
        nplayed+=1;
        if (nplayed == play1_playlist.length) {
            spinner.next();
            h.animate({'marginLeft':ww+500},500, function() {
                document.location= "/finished_experiment";
            });
        } else {
            h.animate({'marginLeft':ww+500},500, function() {
                $(".play_hablando").hide();
                $(".play_callado").show();
                selector.attr('cx',buttons[parseInt(buttons.length/2)].attrs.cx);
                $("#jplayer").stop();
                spinner.next();
                h.delay(300)
                 .hide()
                 .css('margin-left', -h.width() - 100)
                 .show()
                 .animate({'marginLeft':parseInt((ww - h.width())/2) + 'px'},500)
              }
            );
        }
    }
    function stop(yo) {
        $("#" + yo.id).hide();
        $("#" + yo.id.replace('hablando','callado')).show();
        $("#" + yo.id.replace('hablando','loader')).fadeOut();
        $("#jplayer").stop();
    }
    function play(yo) {
        $("#" + yo.id).hide();
        $("#" + yo.id.replace('callado','hablando')).show();
        $("#" + yo.id.replace('callado','loader')).fadeIn();

        var track;
        if (yo.id.substr(1,6) == "play1") {
            track= play1_playlist[nplayed];
        } else {
            track= play2_playlist[nplayed];
        }
        var jplayer= $("#jplayer");
        caching= true;
        jplayer.setFile(track);
        jplayer.play();
        jplayer.volume(0);
        
    }
    function resize() {
            var ww= $(window).width();
            var wh= $(window).height();
            var holder= $("#experiment-wrapper");
            holder.css({'margin-top':parseInt((wh - holder.height())/2 - 30) + 'px',
                        'margin-left':parseInt((ww - holder.width())/2) + 'px'});
            // ,+ 'px'});
//                        'margin-left':(ww - holder.width())/2});// + 'px');
        }
    $(window).resize(resize);
    start_experiment();
    </script>
    </body>
</html>
