<div class="browser" id="browser-year">
  <div class="breadcrumb">
   <?cs each:item = Browser.Path?><a href="<?cs var:Page.PathToRoot ?><?cs var:item.URL?>"><?cs var:item.Name?> &gt;</a><?cs /each?><span><?cs var:Browser.Current?></span>
  </div>
  <div class="yearview gallery ratio-1_1 col-7">
   <?cs each:item = Browser.Items?><div class="item"><div class="content"><?cs if:item.Count?><a href="<?cs var:Page.PathToRoot ?><?cs var:item.URL?>"><span class="main"><?cs var:month(item.Name)?></span><span class="sub"><?cs var:item.Count?> events</span></a><?cs else?><div><span class="main"><?cs var:month(item.Name)?></span></div><?cs /if?></div></div><?cs /each?>
  </div>
  <div style="clear:both"></div>
</div>
