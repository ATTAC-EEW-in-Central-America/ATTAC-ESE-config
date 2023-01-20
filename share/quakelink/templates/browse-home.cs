<div class="browser" id="browser-year">
  <div class="breadcrumb">
   <?cs each:item = Browser.Path?><a href="<?cs var:Page.PathToRoot ?><?cs var:item.URL?>"><?cs var:item.Name?> &gt;</a><?cs /each?><span><?cs var:Browser.Current?></span>
  </div>
  <h1>Event browser</h1><?cs if:Browser.Items.0.Name?>
  <div class="homeview gallery ratio-1_1 col-7">
   <?cs each:item = Browser.Items?><div class="item"><div class="content"><a href="<?cs var:Page.PathToRoot ?><?cs var:item.URL?>"><span class="main"><?cs var:item.Name?></span><span class="sub"><?cs var:item.Count?> events</span></a></div></div><?cs /each?>
  </div><?cs else?>
  <p>Currently no events are available. Check back later.</p><?cs /if?>
</div>
