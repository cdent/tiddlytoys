
$(function() {

        var setupEditEvent = function() {
            $(".tiddler").one("dblclick", function(ev) {
                startEditor(this);
                return false;
                });
        };

        var setupSubmitEvent = function() {
            $('.tiddler').one('dblclick', function(ev) {
                submitEditor(this);
                return false;
                });
        };

        var saveContent = function(content) {
            uri = document.location.href;
            uri = uri.replace(/\.md$/, '');
            tiddler = {};
            tiddler.text = content
            $.ajax({
                url: uri,
                type: "PUT",
                contentType: "application/json",
                data: $.toJSON(tiddler),
                complete: function(xhr, status) {
                    setupEditEvent();
                    formatContent();
                }});
        };

        var formatContent = function() {
            var thing = $('.tiddler').find('pre');
            var content = thing.text();
            thing.hide();
            $('.tiddler').find('#mdformatted').html(markeddown(content)).show();
        };

        var startEditor = function(mdtiddler) {
            var thing = $(mdtiddler).find('pre');
            var content = thing.text();
            $(mdtiddler).find('#mdformatted').hide();
            thing.hide();
            $(mdtiddler).find("textarea").val(content).show();

            setupSubmitEvent();
        };

        var submitEditor = function(mdtiddler) {
            var content = $(mdtiddler).find('textarea').val();
            $(mdtiddler).find('textarea').hide();
            $(mdtiddler).find('pre').html(content);
            saveContent(content);
        };

        var markeddown = function(content) {
            var converter = new Showdown.converter();
            return converter.makeHtml(content);
        };

        var setupExtraDivs = function() {
            $('.tiddler').append('<textarea style="display:none"></textarea>');
            $('.tiddler').append('<div id="mdformatted"></div>');
        };

        setupExtraDivs();
        setupEditEvent();
        formatContent();


});
