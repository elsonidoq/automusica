var Status= function(elem) {
    this.elem= elem;
    this.queue= new Array();
    this.doing_something= false;
    this.can_clear_queue= true;
}
Status.prototype.show_status= function(text) {
    console.log('show_status ' + text);
    //console.log('show_status ' + this.doing_something);
    if (this.doing_something) {
        this.queue.push(text);
        return;
    }
    this.doing_something= true;
    this.elem.text(text);
    var the_this= this;
    console.log("Sliding");
    this.elem.slideDown(500,callback=function() {the_this.set_doing()});
    console.log("Ya Slide");
}

Status.prototype.hide_status= function() {
    console.log('hide_status ');
    //console.log('hide_status ' + this.doing_something);
    if (this.doing_something) {
        this.queue.push(null);
        return;
    }
    this.doing_something= true;
    the_this= this;
    this.elem.slideUp(callback=function() {the_this.set_doing()});
}


Status.prototype.set_doing= function() {
    this.doing_something= (this.queue.length > 0);
    if (this.queue.length > 0) {
        var text= this.queue.pop();
        console.log('Queue ' + text);
        if (text) {
            this.show_status(text);
        } else {
            this.hide_status();
        }
    }
}

