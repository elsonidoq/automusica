var Player = function Player(playlist) {
    this._current_idx = -1;
    this.playlist = playlist;
    this.width = $(window).width();
    this.current_track = null;
}

Player.prototype.play = function(track) {
    console.log(track);
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
    this.play(this.playlist[this._current_idx]);
    this._current_idx++;
}

Player.prototype.has_next= function() {
    return this._current_idx < this.playlist.length;
}

Player.prototype.onSoundComplete = function() {
    $("#playing_img").fadeOut(500, function() {
        $('#stars-container').slideDown(350);
    });
    $("#stars").stars("selectID", -1); //para remover la seleccion
}

Player.prototype.last_played = function() {
    return this.playlist[this._current_idx-1];
}
        

