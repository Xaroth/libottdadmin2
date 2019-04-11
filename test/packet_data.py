PACKETS = {
    'ServerClientInfo': b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
    'ServerClientUpdate': b'\x01\x00\x00\x00\x00\xff',
    'ServerCmdNames': b'\x01G\x00CmdCloneOrder\x00\x01H\x00CmdClearArea'
                      b'\x00\x01I\x00CmdMoneyCheat\x00\x01J\x00CmdChangeBankBalanc'
                      b'e\x00\x01K\x00CmdBuildCanal\x00\x01L\x00CmdCreateSubsi'
                      b'dy\x00\x01M\x00CmdCompanyCtrl\x00\x01N\x00CmdCustomNewsIte'
                      b'm\x00\x01O\x00CmdCreateGoal\x00\x01P\x00CmdRemoveGoal\x00'
                      b'\x01Q\x00CmdSetGoalText\x00\x01R\x00CmdSetGoalProgress\x00'
                      b'\x01S\x00CmdSetGoalCompleted\x00\x01T\x00CmdGoalQuestio'
                      b'n\x00\x01U\x00CmdGoalQuestionAnswer\x00\x01V\x00CmdCreateS'
                      b'toryPage\x00\x01W\x00CmdCreateStoryPageElement\x00\x01X'
                      b'\x00CmdUpdateStoryPageElement\x00\x01Y\x00CmdSetStoryPag'
                      b'eTitle\x00\x01Z\x00CmdSetStoryPageDate\x00\x01[\x00CmdShow'
                      b'StoryPage\x00\x01\\\x00CmdRemoveStoryPage\x00\x01]\x00C'
                      b'mdRemoveStoryPageElement\x00\x01^\x00CmdScrollViewpor'
                      b't\x00\x01_\x00CmdLevelLand\x00\x01`\x00CmdBuildLoc'
                      b'k\x00\x01a\x00CmdBuildSignalTrack\x00\x01b\x00CmdRemoveSig'
                      b'nalTrack\x00\x01c\x00CmdGiveMoney\x00\x01d\x00CmdChangeSet'
                      b'ting\x00\x01e\x00CmdChangeCompanySetting\x00\x01f\x00CmdSe'
                      b'tAutoReplace\x00\x01g\x00CmdCloneVehicle\x00\x01h\x00CmdSt'
                      b'artStopVehicle\x00\x01i\x00CmdMassStartStopVehicl'
                      b'e\x00\x01j\x00CmdAutoreplaceVehicle\x00\x01k\x00CmdDepotSe'
                      b'llAllVehicles\x00\x01l\x00CmdDepotMassAutoReplace'
                      b'\x00\x01m\x00CmdCreateGroup\x00\x01n\x00CmdDeleteGroup'
                      b'\x00\x01o\x00CmdAlterGroup\x00\x01p\x00CmdAddVehicleGr'
                      b'oup\x00\x01q\x00CmdAddSharedVehicleGroup\x00\x01r\x00CmdRe'
                      b'moveAllVehiclesGroup\x00\x01s\x00CmdSetGroupReplaceProtec'
                      b'tion\x00\x01t\x00CmdSetGroupLivery\x00\x01u\x00CmdMoveOrde'
                      b'r\x00\x01v\x00CmdChangeTimetable\x00\x01w\x00CmdSetVehicle'
                      b'OnTime\x00\x01x\x00CmdAutofillTimetable\x00\x01y\x00CmdSet'
                      b'TimetableStart\x00\x01z\x00CmdOpenCloseAirport\x00\x00',
    'ServerCompanyEconomy': b"\x00\xe0'\x00\x00\x00\x00\x00\x00\xa0\x86\x01"
                            b'\x00\x00\x00\x00\x00@\xa1\xfe\xff\xff\xff\xff'
                            b"\xff\n\x00\x01\x00\x00\x00\x00\x00\x00\x00'"
                            b'\x00\x0f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                            b'\x00\x00\x00',
    'ServerCompanyNew': b'\x01',
    'ServerCompanyInfo': b'\x00Braninghall Transport\x00G. Green\x00'
                        b'\x06\x00\x9e\x07\x00\x00\x00\x00\xff\xff\xff\xff',
    'ServerCompanyRemove': b'\x01\x02',
    'ServerCompanyStats': b'\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02'
                         b'\x00\x01\x00\x00\x00\x00\x00\x00\x00',
    'ServerCompanyUpdate': b'\x00Prutown Transport\x00F. A. Gordon 2\x00\x08\x00\x00\xff\xff\xff\xff',
    'ServerChat': b'\x03\x00\x01\x00\x00\x00test\x00\x00\x00\x00\x00\x00\x00\x00\x00',
    'ServerDate': b'\x9b\xde\n\x00',
    'ServerProtocol': b'\x01\x01\x00\x00?\x00\x01\x01\x00A\x00\x01\x02\x00A\x00'
                      b'\x01\x03\x00=\x00\x01\x04\x00=\x00\x01\x05\x00@\x00\x01'
                      b'\x06\x00@\x00\x01\x07\x00\x01\x00\x01\x08\x00@\x00\x01\t'
                      b'\x00@\x00\x00',
    'ServerWelcome': b'Unnamed Server\x001.9.0\x00\x00Random Map\x00\xca\r1'
                     b'k\x00\x1f\xde\n\x00\x00\x01\x00\x01',
    'AdminJoin': b'123qwe\x00libottdadmin2\x000.0.3a1\x00',
    'AdminUpdateFrequency': b'\x06\x00@\x00',
    'AdminPoll': b'\x07\xff\xff\xff\xff',
    'AdminChat': b'\x02\x00\x00\x00\x00\x00This is a test\x00',
    'AdminPing': b'4\x12\x00\x00',

}
