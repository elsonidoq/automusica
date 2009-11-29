<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">
<html lang="en">
<head>
    <title> Experimentando con la percepci&oacute;n musical </title>
	<script type="text/javascript" src="/js/jquery.js"></script>
	<script type="text/javascript" src="/js/ui.core.min.js"></script>
    <script type="text/javascript" src="/js/jquery.jplayer.js"></script>
    

	<style type="text/css">
		#loader {display:none; padding-left:20px; background:url(/images/bigCircleBall.gif) no-repeat center;}
		.play_button_enabled {}
		.play_button_disabled {display:none;}
	</style>


    <!-- jPlayer -->
    <script type="text/javascript">
    $(document).ready(function(){
       var jplayer= $("#jplayer").jPlayer({
/*            ready: function () {
                play('http://lafhis.dc.uba.ar/~pzivic/new_narmour_model/coral_bach_solito.mp3');
            }*/
            swfPath:'/js/'
        })
        .onProgressChange( function(lp,ppr,ppa,pt,tt) {
            if (player.is_muted && lp < 100) {
                console.log("cacheando");
                jplayer.pause();
            } else if(player.is_muted && lp >= 100) {
                console.log("cache termino");
                player.onCacheFinished();
                player.is_muted= false;
                jplayer.volume(100);
                jplayer.playHead(0);
            }
                
        }).onSoundComplete( function() {
            console.log('sound completed');
            player.onSoundComplete();
            
        });


    });
    </script>


	<!-- Star Rating widget stuff here... -->
	<script type="text/javascript" src="/js/ui.stars.js"></script>
	<link rel="stylesheet" type="text/css" href="/css/ui.stars.css"/>
	<link rel="stylesheet" type="text/css" href="/css/crystal-stars.css"/>
    
	<script type="text/javascript">
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
    <style>
        *, html {
            padding:0;
            margin:0;
        }
        
        body {
            font-family: Georgia,Times,"Times New Roman",serif;
            color: #666;
        }
    </style>
</head>
<body style="margin:0 auto;" onload="javascript:resize();">
    <div id="jplayer"></div>
    <input type="hidden" id="visitor_id" value="${visitor_id}"/>
    <div id="content">
        <div id="player" style="position:absolute;top:35%;width:100%">
            <div id="wrapper" style="text-align:center;position:relative;"> 
                <a href="#" class="play_button_enabled" onclick="javascript:player.next()">
                <img border="0" src="/images/play_blue.png"/>
                </a>
                <img border="0" class="play_button_disabled" src="/images/play_gris.png" />
<!--                <span class="track-title" style="font-size:64px;">Nombre de la cancion</span> -->
            </div> 

            <div id="progress" style="height:4px;background:#CCC;">
                <div class="bar" style="width:0px;height:100%;background:#666;">
                </div>
            </div>
            
            <div id="loader"><div style="text-align:center;padding-top: 55px;"></div></div>
            <div id="stars-container" style="width:100%;text-align:center;margin-top:10px;display:none;position:absolute;">
<!--                <span>Como estuvo? &nbsp;&nbsp;</span> -->
                <form id="stars" style="position:relative;width:200px;">
                <!--<form id="stars" action="rate" method="GET" style="position:relative;width:200px;">-->
			<input type="radio" name="rate" value="1" title="Poor" id="rate1" /> <br />
			<input type="radio" name="rate" value="2" title="Fair" id="rate2" /> <br />
			<input type="radio" name="rate" value="3" title="Average" id="rate3" /> <br />
			<input type="radio" name="rate" value="4" title="Good" id="rate4" /> <br />
			<input type="radio" name="rate" value="5" title="Excellent" id="rate5" /> <br />
			<input type="radio" name="rate" value="6" title="Excellent" id="rate6" /> <br />
			<input type="radio" name="rate" value="7" title="Excellent" id="rate7" /> <br />

                </div>
            </div>
        </div>
    </div>
    <script type="text/javascript">
        
        var Player = function Player(playlist) {
            this._current_idx = -1;
            this._playing_interval = null;
            this.playlist = playlist;
            this.width = $(window).width();
            this.current_track = null;
        }
        
        Player.prototype.play = function(track) {
            //console.log('curr_idx', this._current_idx);
            $("#loader").fadeIn();
            $(".play_button_disabled").show();
            $(".play_button_enabled").hide();
            this.current_track = track;
            
            this._do_play(track);
            
        }
        
        Player.prototype.onCacheFinished = function() {
            $("#loader").fadeOut();
        }

        Player.prototype._do_play= function(track) {
            console.log(track);
            var jplayer= $("#jplayer");
            this.is_muted= true;
            jplayer.setFile(track);
            jplayer.play();
            jplayer.volume(0);
        }
        
        Player.prototype.next = function() {
            //TODO: validar limite
            this.play(this.playlist[++this._current_idx]);
        }
        
        Player.prototype.onSoundComplete = function() {
            $("#stars-container").slideDown();
            $("#stars").stars("selectID", -1); //para remover la seleccion
        }
        
        var playlist = ${playlist};
        var player = new Player(playlist);
            
        var onRate = function(ui, type, value) {
            //console.log(data);
            //todo: sacar valor
            /*var next = function() {
                player.next();
            }
            setTimeout(next, 1000);*/
            //console.log(player._current_idx);
            var d= {visitor_id:$("#visitor_id").val(), value: value};
            console.log(d);
            console.log(d.visitor);
            console.log(d.value);
            $.post('/experiment/rated', d , function(data) {

                if (player._current_idx + 1 < player.playlist.length) {
                    $("#stars-container").slideUp();
                    $(".play_button_enabled").show();
                    $(".play_button_disabled").hide();
                } else {
                    document.location= "gracias.html";
                }
            });
        }
        
        var resize = function() {
            var ww = $(window).width();
            $("#content").css('height', $(window).height());
            $("#content").css('height', $(window).height());
            $("#stars").css('left', ww/2 - 100);
            player.width = ww;
        }
        
        $(window).resize(resize);
    </script>
</body>
</html>
