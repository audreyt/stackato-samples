use Mojolicious::Lite;

# Simple route with plain text response
get '/hello' => sub { shift->render_text('Hello World!') };

# Route to template in DATA section
get '/time' => 'clock';

# RESTful web service sending JSON responses
get '/:offset' => sub {
  my $self   = shift;
  my $offset = $self->param('offset') || 23;
  $self->render_json({list => [0 .. $offset]});
};

# Scrape information from remote sites
post '/title' => sub {
  my $self = shift;
  my $url  = $self->param('url') || 'http://mojolicio.us';
  $self->render_text(
    $self->ua->get($url)->res->dom->at('head > title')->text);
};

# WebSocket echo service
websocket '/echo' => sub {
  my $self = shift;
  $self->on_message(sub {
    my ($self, $message) = @_;
    $self->send_message("echo: $message");
  });
};

app->start;
__DATA__

@@ clock.html.ep
% my ($second, $minute, $hour) = (localtime(time))[0, 1, 2];
<%= link_to clock => begin %>
  The time is <%= $hour %>:<%= $minute %>:<%= $second %>.
<% end %>

