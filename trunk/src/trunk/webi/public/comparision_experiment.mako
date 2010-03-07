<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html lang="en">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <link href="/css/comparision_experiment.css" rel="stylesheet" type="text/css" media="screen">

        <script src="/js/raphael.js" type="text/javascript" charset="utf-8"></script>
        <script src="/js/jquery.js" type="text/javascript" charset="utf-8"></script>
        <script src="/js/player.js" type="text/javascript"></script>
        <script src="/js/jquery.jplayer.js" type="text/javascript"></script>
        <script src="/js/hsv2rgb.js" type="text/javascript" charset="utf-8"></script>
        <script src="/js/spinner.js" type="text/javascript" charset="utf-8"></script>
        

        <script type="text/javascript" charset="utf-8">
            var task_status= 0;
            var playing_element= null;
            var buttons= null;
            var texts= {};
            var selector= null;
            var on_drag= false;
            var selected_elements= null;
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
                        return [buttons[i-1], last_distance, texts[i-1]];
                    }
                    last_distance= actual_distance;
                }
                return [buttons[buttons.length-1], last_distance, texts[i-1]]
            }

            function show_interface_description() {
                $("#show_interface_description").fadeOut(500, function(){
                    $("#start_experiment").fadeIn();
                });
                $("#experiment-description").fadeOut(500, function(){
                    $("#interface-description").fadeIn();
                });

            }
            function start_experiment() {
                if (is_test_sound) {
                    var jplayer= $("#jplayer");
                    jplayer.stop();
                    is_test_sound= false;
                }
                $("#descriptions-container").slideUp(500, function() {
/*                    status.show_status('Click para escuchar');*/
                    $("#experiment-wrapper").fadeIn();
                $("#experiment_progress").fadeIn(500);

                $("#next_pair").fadeIn(500);
                });
 /*               if (${ntraining} > 0) {
                   experiment_progress_text.show_status('Practicando');
                } else {
                   experiment_progress_text.show_status('Experimentando');
                }*/
            }
            
                
                

            $(window).mouseup(function(e) {
                if (on_drag) {
                    on_drag= false;
                    $("#holder").unbind('mousemove');
                    var button, distance;
                    var l= find_closest_button(e.clientX - $("#holder").position().left);
                    var button= l[0], distance= l[1], text= l[2];
                    selector.animate({cx:button.attrs.cx, cy:button.attrs.cy}, 100);
                    task_status= task_status | 4;
                    if (task_status == 7) {
                        setTimeout('$("#btn_next").removeAttr("disabled");', 100);
                    }
                }
            });


            function mousedown_handler(e){
                var l= find_closest_button(e.clientX - $("#holder").position().left);
                var button= l[0], distance= l[1];
                selector.animate({cx:button.attrs.cx, cy:button.attrs.cy}, 300);
                task_status= task_status | 4;
                if (task_status == 7) {
                    //$("#btn_next").removeAttr("disabled");
                    setTimeout('$("#btn_next").removeAttr("disabled");', 100);
                }
                
            } 
            $(document).ready(function() {
               var jplayer= $("#jplayer").jPlayer({
                    ready: function () {



                    }
                    ,swfPath:'/js'
                })
               .onProgressChange( function(lp,ppr,ppa,pt,tt) {
                    if(caching && lp >= 100) {
                        $(".loader").fadeOut();
                        caching= false;
                        jplayer.volume(100);
                        jplayer.playHead(0);
                        
                    } 
                        
                }).onSoundComplete( function() {
                    if (is_test_sound) {
                        is_test_sound= false;
                    } else {
                        $(".play_hablando").hide();
                        $(".play_callado").show();
                        if (playing_element.id.substr(0,5) == "play1") {
                            $("#" + playing_element.id.replace('1', '2')).css('cursor', 'default');
                            task_status= task_status | 1;
                        } else {
                            $("#" + playing_element.id.replace('2', '1')).css('cursor', 'default');
                            task_status= task_status | 2;
                        }
                        playing_element= null;
                        if (task_status == 7) {
                            $("#btn_next").removeAttr('disabled');
                        }
                    }

                    
                });
            });

            var sound_test = function() {
                var track= "${test_sound}";
                var jplayer= $("#jplayer");
                is_test_sound= true;
                jplayer.setFile(track);
                jplayer.play();
            }

            window.onload = function () {
                spinner= new Spinner("experiment_progress", 10, 40, play1_playlist.length, 2, "#fff", "#abb1f0", ntraining, "#fff", "#cfabf0");
            
                resize();
                var W = 640,
                    H = 100,
                    values = [],
                    len = 9;
                for (var i = len; i--;) {
                    values.push(50);
                }
                r = Raphael("holder", W, H);
                var rectangle= r.rect(0, 0, W, H).attr({stroke:"none", fill:"#fff", opacity:0}).mousedown(mousedown_handler);
                r.safari();
                
                function translate(x, y) {
                    return [
                        20 + (W-40) / (values.length - 1) * x,
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
                        buttons[buttons.length-1].node.style.cursor="pointer";
                    })(i, xy);
                    if (i == ii - 1) {
                        f(i + 1, xy1);
                    }
                }
                var selector_xy= translate(4, values[4]);
                selector= r.circle(selector_xy[0], selector_xy[1] - 30, 13).attr({'fill':'#869af0', 'fill-opacity':0.3, stroke:'none'});
                selector.node.style.cursor= 'move';
                selector.mousedown(function(e) {
                    on_drag= true;
                    h= $("#holder");
                    h.mousemove(function(e) {
                        var y= e.clientY - h.position().top;
                        var x= e.clientX - h.position().left;
                        selector.animate({cx:x, cy:buttons[0].attrs.cy}, 100);
                    });
                });
                $("#holder").mousedown(mousedown_handler);
                buttons.mousedown(mousedown_handler);

                texts[4]= r.text(buttons[4].attrs.cx, buttons[4].attrs.cy + 3, "=").attr({fill:"#fff"}).mousedown(mousedown_handler);
                texts[0]= r.text(buttons[0].attrs.cx, buttons[4].attrs.cy + 3, "+").attr({fill:"#fff"}).mousedown(mousedown_handler);
                texts[8]= r.text(buttons[8].attrs.cx, buttons[4].attrs.cy + 3, "+").attr({fill:"#fff"}).mousedown(mousedown_handler);
                selected_elements= [buttons[4], texts[4]];
                texts[4].node.style.cursor = "pointer";
                texts[0].node.style.cursor = "pointer";
                texts[8].node.style.cursor = "pointer";
            };
        </script>
    </head>
    <body style="margin:0 auto;" >
        <script src="/js/wz_tooltip.js" type="text/javascript" ></script>  

        <input type="hidden" id="visitor_id" value="${visitor_id}"/>
        <div  id="experiment_progress" > 
            <div style="display:none;" id="experiment_progress_text"></div>
        </div>
        <div id="descriptions-container">
        <div class="description" id="experiment-description" >
            ${experiment_description}
        </div>
        <div class="description" id="interface-description" style="display:none;" >
            ${interface_description}
        </div>
        <div id="comenzar">
            <a id="show_interface_description" style="display:none;" href="#" onclick="javascript:show_interface_description();">siguiente</a>
            <a id="start_experiment" href="#" onclick="javascript:start_experiment();">comenzar</a>
        </div>
        </div>

        <div id="jplayer"></div>

        <div id="experiment-wrapper" >
            <div id="holder" style="display:inline;"> </div>
            <div id="play1" style="display:inline;float:left;margin-top:-88px;margin-left:-80px;height:60px;width:60px;">
                <img class="play_callado" id="play1_callado" style="height:100%;width:100%;cursor:pointer;" 
                     src="/images/speaker_callado.png" onclick="javascript:play(this)"/> 
                <img class="play_hablando" id="play1_hablando" style="display:none;height:100%;width:100%;" 
                     src="/images/speaker_hablando.png" /> 
                <div style="font-size:10px;text-align:center;">click para escuchar</div> 
                <div class="loader" id="play1_loader" style="display:none;text-align:center;"> <img src="/images/loader.gif"/> </div>
            </div>
            <div id="play2" style="margin-top:-88px;margin-right:-80px;float:right;height:60px;width:60px;">
                <img class="play_callado" id="play2_callado" style="height:100%;width:100%;cursor:pointer;" 
                     src="/images/speaker_callado.png" onclick="javascript:play(this)"/> 
                <img class="play_hablando" id="play2_hablando" style="display:none;height:100%;width:100%;" 
                     src="/images/speaker_hablando.png" /> 
                <div style="font-size:10px;text-align:center;">click para escuchar</div> 
                <div class="loader" id="play2_loader" style="display:none;text-align:center;"> <img src="/images/loader.gif"/> </div>
            </div>
        </div>
        <div id="next_pair" style="display:none;text-align:center;margin-top:150px;">
        <input style="font-size:20px" type="button" onclick="javascript:next()" value="Siguiente" id="btn_next" disabled="disabled" /> 
            <div style="display:inline">
            <img id="question_image" src="/images/question.png" >
        </div>
    <script type="text/javascript">

    $("#question_image").mouseenter(function() {
        Tip('Para habilitar el bot&oacute;n ten&eacute;s que<br>escuchar al menos una vez cada<br>canci&oacute;n y expresar tu preferencia<br>poniendo el selector en alguna<br>parte de la barra');    
    }).mouseout(function() {
        UnTip();
    });
    function next() {
        var h= $("#experiment-wrapper");
        var ww= $(window).width();
        task_status= 0;
        nplayed+=1;
        if (nplayed == play1_playlist.length) {
            spinner.next();
            h.animate({'marginLeft':-h.width()},500, function() {
                document.location= "/finished_experiment";
            });
        } else {
            $("#btn_next").attr('disabled', true);
            h.animate({'marginLeft':-h.width()},500, function() {
                $(".play_hablando").hide();
                $(".play_callado").show();
                selector.attr('cx',buttons[parseInt(buttons.length/2)].attrs.cx);
                selector.attr('cy',buttons[0].attrs.cy - 30);
                $("#jplayer").stop();
                spinner.next();
                h.delay(300)
                 .hide()
                 .css('margin-left', ww + 150)
                 .show()
                 .animate({'marginLeft':parseInt((ww - h.width())/2) + 'px'},700)
              }
            );
        }
    }
    function play(yo) {
        if(playing_element) {
            return;
        }
        playing_element= yo;
        $("#" + yo.id).hide();
        $("#" + yo.id.replace('callado','hablando')).show();
        $("#" + yo.id.replace('callado','loader')).fadeIn();

        var track;
        if (yo.id.substr(0,5) == "play1") {
            $("#" + yo.id.replace('1', '2')).css('cursor', 'default');
            track= play1_playlist[nplayed];
        } else {
            $("#" + yo.id.replace('2', '1')).css('cursor', 'default');
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
            holder.css({'margin-top':parseInt((wh - holder.height())/2 - 100) + 'px',
                        'margin-left':parseInt((ww - holder.width())/2) + 'px'});

        }
    $(window).resize(resize);
    start_experiment();
    </script>
    </body>
</html>
