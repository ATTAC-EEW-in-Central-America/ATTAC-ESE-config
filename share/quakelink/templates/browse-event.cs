<div class="browser" id="browser-day">
	<div class="breadcrumb">
		<?cs each:item = Browser.Path?><a href="<?cs var:Page.PathToRoot ?><?cs var:item.URL?>"><?cs var:item.Name?> &gt;</a><?cs /each?><span><?cs var:Browser.EventID?></span>
	</div>
	<table id="revlist" class="bordered striped">
		<thead>
			<tr>
				<th class="text-center" title="Sequential update number"><strong>Revision</strong></th>
				<th class="text-center" title="Time the event update was received by the QuakeLink server"><strong>Updated</strong><br/>UTC</th>
				<th class="text-center" title="Time of the event"><strong>Origin Time</strong><br/>UTC</th>
				<th class="text-center" title="Magnitude"><strong>Mag</strong></th>
				<th class="text-center" title="Magnitude Type"><strong>Mag<br/>Type</strong></th>
				<th class="text-center"><strong>Latitude</strong><br/>degrees</th>
				<th class="text-center"><strong>Longitude</strong><br/>degrees</th>
				<th class="text-center"><strong>Depth</strong><br/>km</th>
				<th class="text-center" title="Number stations participating in the hypocenter solution"><strong>Phases</strong></th>
				<th class="text-center" title="Agency ID read from event or alternatively from origin context"><strong>Agency</strong></th>
				<th class="text-center" title="Evaluation mode and status encoded into a single state flag"><strong>S</strong></th>
				<th class="text-center" title="Event type"><strong>Event<br/>Type</strong></th>
				<th class="text-left"><strong>Region Name</strong></th>
				<th class="text-center" title="Download event XML"><strong>XML</strong></th>
			</tr>
		</thead>
		<tbody><?cs each:item = Browser.Items?>
			<tr>
				<td class="text-right"><?cs var:float(item.Rev,0)?></td>
				<td class="text-center"><?cs var:item.UT?></td>
				<td class="text-center"><?cs var:item.OT?></td>
				<td class="text-center" title="<?cs var:item.Mag?>"><?cs var:float(item.Mag, 1)?></td>
				<td class="text-center"><?cs var:item.MagT?></td>
				<td class="text-right" title="<?cs var:item.Lat?>"><?cs var:strfcoord(item.Lat,"%.2F°%c")?></td>
				<td class="text-right" title="<?cs var:item.Lon?>"><?cs var:strfcoord(item.Lon,"%.2F°%C")?></td>
				<td class="text-right" title="<?cs var:item.Dep?>"><?cs var:float(item.Dep,0)?></td>
				<td class="text-center"><?cs var:item.Phases?></td>
				<td class="text-center"><?cs var:item.Agency?></td>
				<td class="text-center <?cs var:evalModeFlag(item.EMode, item.Status)?>" title="<?cs var:item.EMode?> <?cs var:item.EStatus?>"><?cs var:evalStatusFlag(item.EStatus, item.Stat)?></td>
				<td class="text-center"><?cs var:item.Type?></td>
				<td class="text-left"><?cs var:item.Reg?></td>
				<td class="text-center">
					<a href="<?cs var:Page.PathToRoot?><?cs var:Page.EventsQueryPath?>?id=<?cs var:Browser.EventID?>&rev=<?cs var:float(item.Rev,0)?>&download" title="Preferred magnitude and origin without arrivals">P</a>&nbsp;/&nbsp;<a href="<?cs var:Page.PathToRoot?><?cs var:Page.EventsQueryPath?>?id=<?cs var:Browser.EventID?>&rev=<?cs var:float(item.Rev,0)?>&include=all&download" title="All magnitudes of preferred origin including picks, arrivals, amplitudes and station magnitudes">A</a>
				</td>
			</tr><?cs /each?>
		</tbody>
	</table>
</div>
