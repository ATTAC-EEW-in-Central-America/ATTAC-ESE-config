<div class="browser" id="browser-day">
	<div class="breadcrumb">
		<?cs each:item = Browser.Path?><a href="<?cs var:Page.PathToRoot?><?cs var:item.URL?>"><?cs var:item.Name?> &gt;</a><?cs /each?><span><?cs var:Browser.Current?></span>
	</div>
	<table id="list" class="bordered striped hover">
		<thead >
			<tr>
				<th class="text-center" title="Event ID and last update time"><strong>Event ID</strong></th>
				<th class="text-center" title="Time of the event"><strong>Origin Time</strong><br/>UTC</th>
				<th class="text-center" title="Magnitude and type"><strong>Mag</strong></th>
				<th class="text-center"><strong>Latitude</strong><br/>degrees</th>
				<th class="text-center"><strong>Longitude</strong><br/>degrees</th>
				<th class="text-center"><strong>Depth</strong><br/>km</th>
				<th class="text-center" title="Agency ID read from event or alternatively from origin context"><strong>Agency</strong></th>
				<th class="text-center" title="Evaluation mode and status encoded into a single state flag"><strong>S</strong></th>
				<th class="text-center" title="Focal mechanism solution"><strong>FM</strong></th>
				<th class="text-left"><strong>Region Name</strong></th>
				<th class="text-center" title="Download event XML"><strong>XML</strong></th>
			</tr>
		</thead>
		<tbody><?cs each:item = Browser.Items?>
			<tr onclick="document.location = '<?cs var:Page.PathToRoot ?><?cs var:item.URL?>';">
				<td class="text-center" title="Last updated at <?cs var:item.UT?>"><?cs var:item.ID?></td>
				<td class="text-center"><?cs var:item.OT?></td>
				<td class="text-center" title="<?cs var:item.Mag?><?cs if:item.MagT?> (<?cs var:item.MagT?>)<?cs /if?>"><?cs var:float(item.Mag,1)?></td>
				<td class="text-right" title="<?cs var:item.Lat?>"><?cs var:strfcoord(item.Lat, "%.2F°%c")?></td>
				<td class="text-right" title="<?cs var:item.Lon?>"><?cs var:strfcoord(item.Lon,"%.2F°%C")?></td>
				<td class="text-right" title="<?cs var:item.Dep?>"><?cs var:float(item.Dep,0)?></td>
				<td class="text-center"><?cs var:item.Agency?></td>
				<td class="text-center <?cs var:evalModeFlag(item.EMode, item.Status)?>" title="<?cs var:item.EMode?> <?cs var:item.EStatus?>"><?cs var:evalStatusFlag(item.EStatus, item.Stat)?></td><?cs if:item.FM?>
				<td class="text-center" title="<?cs #
					?>Strike/dip/rake:&#9;<?cs var:item.FM.Strike?>/<?cs var:item.FM.Dip?>/<?cs var:item.FM.Rake?><?cs if:item.FM.OT
					?>&#10;Origin time:&#9;<?cs var:item.FM.OT?><?cs /if?><?cs if:item.FM.Lat
					?>&#10;Latitude:&#9;&#9;<?cs var:item.FM.Lat?><?cs /if?><?cs if:item.FM.Lon
					?>&#10;Longitude:&#9;&#9;<?cs var:item.FM.Lon?><?cs /if?><?cs if:item.FM.Dep
					?>&#10;Depth:&#9;&#9;&#9;<?cs var:item.FM.Dep?><?cs /if?><?cs if:item.FM.Mag
					?>&#10;Magnitude:&#9;&#9;<?cs var:item.FM.Mag?><?cs /if?><?cs if:item.FM.Agency
					?>&#10;Agency:&#9;&#9;<?cs var:item.FM.Agency?><?cs /if?><?cs #
					?>">&#10004;</td><?cs else?><td/><?cs /if?>
				<td><?cs var:item.Reg?></td>
				<td class="text-center">
					<a href="<?cs var:Page.PathToRoot?><?cs var:Page.EventsQueryPath?>?id=<?cs var:item.ID?>&download" title="Preferred magnitude and origin without arrivals">P</a>&nbsp;/&nbsp;<a href="<?cs var:Page.PathToRoot?><?cs var:Page.EventsQueryPath?>?id=<?cs var:item.ID?>&include=all&download" title="All magnitudes of preferred origin including picks, arrivals, amplitudes and station magnitudes">A</a>
				</td>
			</tr><?cs /each?>
		</tbody>
	</table>
</div>
