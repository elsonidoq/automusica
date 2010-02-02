<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">
<html lang="en">
<head>
    <title> Experimentando con la percepci&oacute;n musical </title>

    <!-- jPlayer -->
    <script type="text/javascript">
    var playlist = ${playlist};
    var nplayed = ${nplayed};
    if(${resume_experiment}) {
        if(nplayed >= playlist.length) {
            document.location= "/finished_experiment";
        }
    }
    </script>

    <script src="/js/status.js" type="text/javascript" charset="utf-8"></script>
    <script src="/js/raphael.js" type="text/javascript" charset="utf-8"></script>
    <script src="/js/spinner.js" type="text/javascript" charset="utf-8"></script>
	<script src="/js/jquery.js" type="text/javascript"></script>
	<script src="/js/ui.core.min.js" type="text/javascript"></script>
    <script src="/js/jquery.jplayer.js" type="text/javascript"></script>
    <script src="/js/player.js" type="text/javascript"></script>

    <script type="text/javascript">
    
    var spinner= null;
    $(document).ready(function(){
       var jplayer= $("#jplayer").jPlayer({
            ready: function () {



            }
            ,swfPath:'/js'
        })
        .onProgressChange( function(lp,ppr,ppa,pt,tt) {
            if (player.is_muted && lp < 100) {
                var lp= parseInt(lp);
                if (lp % 10 == 0)  {
                    $("#loader_bar").animate({"width":lp+"%"});
                }
            } else if(player.is_muted && lp >= 100) {
                $("#loader_bar").animate({"width":"100%"});
                //console.log("cache termino");
                player.is_muted= false;
                jplayer.volume(100);
                jplayer.playHead(0);
                
                status.hide_status();
                $("#loader_bar").fadeOut(500, function() {
                    $('#playing_img').fadeIn();
                });
            } 
                
        }).onSoundComplete( function() {
            //console.log('sound completed');
            if (!is_test_sound)
                player.onSoundComplete();
            else
                is_test_sound= false;
            
        });



    });
    </script>


	<!-- Star Rating widget stuff here... -->
	<script type="text/javascript" src="/js/ui.stars.js"></script>
	<link rel="stylesheet" type="text/css" href="/css/ui.stars.css"/>
	<link rel="stylesheet" type="text/css" href="/css/crystal-stars.css"/>
	<link rel="stylesheet" type="text/css" href="/css/experiment.css"/>
    
	<script type="text/javascript">
        var onRate = function(ui, type, value) {
            var d= {experiment_id:experiment_id, 
                    visitor_id:$("#visitor_id").val(), 
                    track:player.last_played(), 
                    value: value};

            $.post('/experiment/rated', d , function(data) {

                spinner.next()
                if (spinner.actual_sector == spinner.ntraining) {
                    experiment_progress_text.show_status('Experimentando');
                }

                if (player.has_next()) {
                    $("#stars-container").slideUp(callback=function() {
                        enable_play();
                        status.show_status('Click para escuchar');
                    });
                } else {
                    setTimeout("document.location= '/questions?visitor_id=${visitor_id}';", 500);
                }
            });
        }

		$(function(){
			$("#stars").children().not(":radio").hide();
			$("#stars").stars({
				callback: onRate 
			});
        $("#stars").data("stars").$cancel.hide();
		});
	</script>

    <!-- CSS -->
	<link rel="stylesheet" type="text/css" href="/css/demos.css"/>
</head>
<body style="margin:0 auto;" onload="javascript:resize();">
        <div id="description">
        <div id="description_container" >
            ${experiment_description}
        </div>
        <div id="comenzar">
            <a id="a_comenzar" href="#" onclick="javascript:start_experiment();">comenzar</a>
        </div>
        </div>
    <div id="jplayer"></div>
    <input type="hidden" id="visitor_id" value="${visitor_id}"/>
    <div id="content">
        <div style="align:right;width:100%">
            <div style="text-align:center;" id="experiment_progress" > 
                <div style="display:none;" id="experiment_progress_text"></div>
            </div>
        </div>
        <div id="player">
            <div id="wrapper"> 
                <img id="play_button_enabled" onclick="javascript:next_song();" border="0" src="/images/play_blue.png"/>
                <img border="0" id="play_button_disabled" src="/images/play_gris.png" />
            </div> 

            <div id="loader-wrapper">
                <div id="loader">
                    <div id="loader_bar">
                    </div>
                </div>
            </div>
            <div id="stars-container">
                <form id="stars">
                    <input type="radio" name="rate" value="1" title="Poor" id="rate1" /> <br />
                    <input type="radio" name="rate" value="2" title="Fair" id="rate2" /> <br />
                    <input type="radio" name="rate" value="3" title="Average" id="rate3" /> <br />
                    <input type="radio" name="rate" value="4" title="Good" id="rate4" /> <br />
                    <input type="radio" name="rate" value="5" title="Excellent" id="rate5" /> <br />
                </form>                    
            </div>

            <div id="loader-text">
            </div>
            <div id="playing_img" style="text-align:center" > <img src="/images/sound_blue.png" /> </div>
            
        </div>
    </div>
    <script type="text/javascript">
        
        var next_song= function() {
            var d= {experiment_id:experiment_id, 
                    visitor_id:$("#visitor_id").val(), 
                    track:player.playlist[player._current_idx]};
            
            player.next();
            $.post('/experiment/played', d ); 
        }

        var enable_play= function() {
            $("#play_button_enabled").show();
            $("#play_button_disabled").hide();
        }

        var disable_play= function() {
            $("#play_button_disabled").show();
            $("#play_button_enabled").hide();
        }
        

        var start_experiment = function() {
            if (is_test_sound) {
                var jplayer= $("#jplayer");
                jplayer.stop();
                is_test_sound= false;
            }
            $("#description").slideUp(500, function() {
                enable_play();
                status.show_status('Click para escuchar');
            });
            $("#experiment_progress").fadeIn(500);
            experiment_progress_text.show_status('Practicando');
        }
        
        
        var sound_test = function() {
            var track= "${test_sound}";
            var jplayer= $("#jplayer");
            is_test_sound= true;
            jplayer.setFile(track);
            jplayer.play();
        }

        var parse_qs = function () {
            var equalities= document.location.search.substring(1).split("&");
            var res= {};
            for (var i in equalities) {
                eq= equalities[i];
                l= eq.split("=");
                res[l[0]]= l[1];
            }
            return res;
        }

        var resize = function() {
            var ww = $(window).width();
            $("#content").css('height', $(window).height());
            $("#content").css('height', $(window).height());
            $("#stars").css('left', ww/2 - 28*5/2 + 2);
            $("#loader").css({'margin-left': ww/2 - $("#play_button_enabled").width()/2 ,
                                       'width'       : $("#play_button_enabled").width()-40});
/*            description_frame_heigh=$("#description").height();
            $("#description_container").css('height',description_frame_heigh-40);*/
            player.width = ww;
        }
        
        var player = new Player(playlist);
        player._current_idx= nplayed;

        var click_to_start_to= null;
        var status= new Status($("#loader-text"));
        var experiment_progress_text= new Status($("#experiment_progress_text"));
        var is_test_sound = false;
        var experiment_id= parse_qs()['id'];

        var spinner= new Spinner("experiment_progress", 10, 40, playlist.length, 2, "#fff", "#abb1f0", 
                                    ${ntraining}, "#fff", "#cfabf0");
        spinner._ntraining= ${ntraining};
            
        if(${resume_experiment}) {
            if(!player.has_next()) {
                document.location= "/finished_experiment";
            } else {
                enable_play();
                status.show_status('Resumiendo experimento');
                $("#experiment_progress").fadeIn(500);

                click_to_start_to= setTimeout("if($('#loader-text').is(':visible')) {status.show_status('Click para escuchar');}",1000);
                for (var i=1; i<=nplayed; i++){
                    spinner.next();
                }
                if(spinner.in_training()) {
                    experiment_progress_text.show_status('Practicando');
                } else {
                    experiment_progress_text.show_status('Experimentando');
                }
                        
            }
        } else {
            $("#description").show();
            disable_play();
        }


        $(window).resize(resize);
    </script>
</body>
</html>
