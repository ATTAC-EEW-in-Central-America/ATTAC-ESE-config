<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html>
<head><?cs var:Page.Head ?>
 <link rel="stylesheet" type="text/css" href="<?cs var:Page.PathToRoot ?>/media/style.css"/>
 <link rel="icon" type="image/x-icon" href="<?cs var:Page.PathToRoot ?>/media/images/favicon.ico"/>
 <title><?cs var:Page.Title ?></title>
</head>
<body>
	<header>
		<div class="container">
			<div class="content compact">
				<h1>QuakeLink</h1>
				<h2><?cs var:QL.version ?></h2>
			</div>
		</div>
	</header>
	<nav class="top overlay">
		<div class="container">
			<div class="content">
				<ul class="menu">
					<?cs each:item = Site.Pages?><li><a href="<?cs var:Page.PathToRoot ?>/<?cs var:item.URL ?>"><?cs var:item.Name ?></a></li><?cs /each?>
				</ul>
			</div>
		</div>
	</nav>
	<section>
		<article>
			<div class="content">
				<?cs var:Page.Content ?>
			</div>
		</article>
	</section>
	<footer>
		<div class="container">
			Copyright &copy; <a href="http://www.gempa.de">gempa GmbH</a>
		</div>
	</footer>
</body>
</html>
