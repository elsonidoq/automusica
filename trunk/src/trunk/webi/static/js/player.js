var Player = function Player(playlist) {
    this._current_idx = -1;
    this.playlist = playlist;
    this.width = $(window).width();
    this.current_track = null;
}

Player.prototype.play = function(track) {
    disable_play();
    this.current_track = track;
    
    var jplayer= $("#jplayer");
    $("#loader_bar").css({"width":0});
    $("#loader_bar").show();
    $("#loader").show();

    status.show_status('Cargando');

    this.is_muted= true;
    jplayer.setFile(track);
    jplayer.play();
    jplayer.volume(0);
}

Player.prototype.next = function() {
    //TODO: validar limite
    if (click_to_start_to) {
        clearTimeout(click_to_start_to);
        click_to_start_to= null;
    }
    this.play(this.playlist[++this._current_idx]);
}

Player.prototype.onSoundComplete = function() {
    $("#playing_img").fadeOut(500, function() {
        $('#stars-container').slideDown(350);
    });
    $("#stars").stars("selectID", -1); //para remover la seleccion
}

var onRate = function(ui, type, value) {
    var d= {experiment_id:experiment_id, visitor_id:$("#visitor_id").val(), track:player.playlist[player._current_idx-1], value: value};
    $.post('/experiment/rated', d , function(data) {

        spinner.next()
        if (player._current_idx < player.playlist.length) {
            $("#stars-container").slideUp(callback=function() {
                enable_play();
                status.show_status('Click para escuchar');
            });
        } else {
            setTimeout("document.location= '/finished_experiment';", 500);
        }
    });
}

